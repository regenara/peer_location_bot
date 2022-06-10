import asyncio
import logging
import ssl
from collections import deque
from datetime import (datetime,
                      timedelta)
from typing import (Any,
                    Deque,
                    Dict,
                    List,
                    Tuple,
                    Union)
from urllib.parse import urljoin

import certifi
import ujson
from aiohttp import (ClientSession,
                     ClientTimeout,
                     TCPConnector)
from aiohttp.client_exceptions import ContentTypeError
from asyncio_throttle import Throttler
from pytz import timezone

from db_models.applications import Application
from utils.cache import cache


class IntraAPIError(Exception):
    """"""


class UnknownIntraError(IntraAPIError):
    """"""


class NotFoundIntraError(IntraAPIError):
    """"""


class TimeoutIntraError(IntraAPIError):
    """"""


class IntraAPI:
    def __init__(self, config):
        self._apps: Deque[Dict[str, Any]] = deque()
        self._base_url = 'https://api.intra.42.fr/v2/'
        self._auth_url = 'https://api.intra.42.fr/oauth/token'
        self._config = config
        self._refresher = None
        self._logger = logging.getLogger('IntraAPI')

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = TCPConnector(ssl=ssl_context)
        timeout: ClientTimeout = ClientTimeout(total=60)
        self.session: ClientSession = ClientSession(connector=connector, json_serialize=ujson.dumps, timeout=timeout)
        self._throttler = Throttler(rate_limit=20)

    async def _request_token(self, params: Dict[str, str]) -> str:
        async with self.session.request('POST', self._auth_url, params=params) as response:
            if response.status == 200:
                js = await response.json()
                return js['access_token']

    async def _get_token(self, application_id: int, client_id: str, client_secret: str) -> str:
        params = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        access_token = await self._request_token(params=params)
        self._logger.info('Get token=%s from application=%s', access_token, application_id)
        return access_token

    async def _request(self, endpoint: str, params: dict = None,
                       personal_access_token: str = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        url = urljoin(self._base_url, endpoint)
        params = params or {}
        self._apps.rotate(int(not personal_access_token))
        async with self._throttler:
            attempts = 1
            while attempts < 10:
                app = self._apps[0]
                access_token = personal_access_token or app['access_token']
                params = {**params, 'access_token': access_token}
                try:
                    async with self.session.request('GET', url, params=params) as response:

                        if response.status == 200:

                            try:
                                json_response = await response.json()
                                self._logger.info('Request=%s %s [%s] | %s | %s | completed',
                                                  attempts, response.reason, response.status, url, access_token)
                                return json_response
                            except ContentTypeError as e:
                                self._logger.error('Request=%s %s [%s] | %s | %s | ContentTypeError %s | continue',
                                                   attempts, response.reason, response.status, url, access_token, e)
                                continue

                        if response.status == 429 and endpoint == 'me':
                            self._logger.error('Request=%s %s [%s] | %s | %s | continue',
                                               attempts, response.reason, response.status, url, access_token)
                            continue

                        if response.status == 401 and (await response.json()).get(
                                'message') == 'The access token expired':
                            self._logger.error('Request=%s %s [%s] | %s | %s | token expired | refresh, reset attempts',
                                               attempts, response.reason, response.status, url, access_token)
                            self._apps[0]['access_token'] = await self._get_token(application_id=app['id'],
                                                                                  client_id=app['client_id'],
                                                                                  client_secret=app['client_secret'])
                            attempts = 1

                        if response.status == 404:
                            self._logger.error('Request=%s %s [%s] | %s | %s | raise NotFoundIntraError',
                                               attempts, response.reason, response.status, url, access_token)
                            raise NotFoundIntraError(f'Intra response: {response.reason} [{response.status}]')

                        self._logger.error('Request=%s %s [%s] | %s | %s | continue',
                                           attempts, response.reason, response.status, url, access_token)
                        attempts += 1
                        self._apps.rotate(1)

                except asyncio.exceptions.TimeoutError:
                    self._logger.error('Request=%s | %s | raise TimeoutIntraError', attempts, url)
                    raise TimeoutIntraError(f'Intra does not respond for more than 60 seconds')

                except TypeError as e:
                    self._logger.error('Request=%s | %s | %s | TypeError, raise UnknownIntraError', attempts, url, e)
                    raise UnknownIntraError('Something went wrong, please try again')

            self._logger.error('Request=%s %s [%s] | %s | %s | raise UnknownIntraError',
                               attempts, response.reason, response.status, url, access_token)
            raise UnknownIntraError(f'Intra response: {response.reason} [{response.status}]')

    async def load(self):
        applications = await Application.get_all() if not self._config.test else [await Application.get_test()]
        self._apps = deque(maxlen=len(applications))
        for application in applications:
            access_token = await self._get_token(application_id=application.id,
                                                 client_id=application.client_id,
                                                 client_secret=application.client_secret)
            self._apps.append({**application.to_dict(), 'access_token': access_token})

    async def auth(self, client_id: str, client_secret: str, code: str) -> str:
        params = {
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': self._config.bot_base_url
        }
        return await self._request_token(params=params)

    async def get_me(self, personal_access_token: str) -> Dict[str, Any]:
        endpoint = 'me'
        return await self._request(endpoint, personal_access_token=personal_access_token)

    @cache(ttl=120)
    async def get_peer(self, login: str) -> Dict[str, Any]:
        endpoint = f'users/{login}'
        return await self._request(endpoint)

    @cache(ttl=3600)
    async def get_peers(self, logins: List[str]) -> List[Dict[str, Any]]:
        endpoint = f'users'
        return await self._request(endpoint, params={'filter[login]': ','.join(logins)})

    @cache(ttl=3600)
    async def get_peer_coalitions(self, login: str) -> List[Dict[str, Any]]:
        endpoint = f'users/{login}/coalitions_users'
        return await self._request(endpoint)

    @cache(ttl=300)
    async def get_peer_locations(self, login: str, all_locations: bool) -> List[Dict[str, Any]]:
        endpoint = f'users/{login}/locations'
        if not all_locations:
            return await self._request(endpoint, params={'per_page': 50})
        locations = []
        page = 1
        params = {
            'page': page,
            'per_page': 100
        }
        data = await self._request(endpoint, params=params)
        locations.extend(data)
        while data:
            page += 1
            params['page'] = page
            data = await self._request(endpoint, params=params)
            locations.extend(data)
        return locations

    @cache(ttl=3600)
    async def get_peer_feedbacks(self, login: str) -> List[Dict[str, Any]]:
        endpoint = f'users/{login}/scale_teams/as_corrector'
        return await self._request(endpoint, params={'per_page': 50})

    async def get_coalition(self, coalition_id: int) -> Dict[str, Any]:
        endpoint = f'coalitions/{coalition_id}'
        return await self._request(endpoint)

    @cache(ttl=300)
    async def get_location_history(self, host: str) -> List[Dict[str, Any]]:
        endpoint = 'locations'
        return await self._request(endpoint, params={'filter[host]': host, 'per_page': 10})

    async def get_campus(self, campus_id: int) -> Dict[str, Any]:
        endpoint = f'campus/{campus_id}'
        return await self._request(endpoint)

    async def get_campuses(self) -> List[Dict[str, Any]]:
        endpoint = f'campus'
        return await self._request(endpoint, params={'per_page': 100})

    async def get_cursus(self) -> List[Dict[str, Any]]:
        endpoint = f'cursus'
        return await self._request(endpoint, params={'per_page': 100})

    async def get_project(self, project_id: int) -> Dict[str, Any]:
        endpoint = f'projects/{project_id}'
        return await self._request(endpoint)

    @cache(ttl=300)
    async def get_events(self, campus_id: int, cursus_id: int) -> List[Dict[str, Any]]:
        endpoint = f'campus/{campus_id}/cursus/{cursus_id}/events'
        params = {'filter[future]': 'true'}
        return await self._request(endpoint, params=params)

    @cache(ttl=300)
    async def get_exams(self, campus_id: int, cursus_id: int) -> List[Dict[str, Any]]:
        endpoint = f'campus/{campus_id}/cursus/{cursus_id}/exams'
        data = await self._request(endpoint)
        exams_data = []
        exams_ids = []
        for exam in data:
            if (datetime.fromisoformat(exam['begin_at'].replace('Z', '+00:00')) > datetime.now(tz=timezone('UTC'))) \
                    and exam['id'] not in exams_ids:
                exams_data.append(exam)
                exams_ids.append(exam['id'])
        return exams_data

    @cache(ttl=3600)
    async def get_project_peers(self, project_id: int, campus_id: int,
                                time_zone: str) -> Tuple[int, List[Dict[str, Any]]]:
        endpoint = f'projects/{project_id}/projects_users'
        project_data = []
        weeks = 4
        weeks_count = weeks
        ids = []
        while len(project_data) < 30 and weeks < 37:
            weeks_count = weeks
            now = datetime.now(timezone(time_zone))
            past = now - timedelta(weeks=weeks)
            params = {
                'filter[campus]': campus_id,
                'per_page': 100,
                'range[marked_at]': f'{past},{now}',
                'range[final_mark]': '40,150'
            }
            data = await self._request(endpoint, params=params)
            [[project_data.append(record), ids.append(record['id'])] for record in data
             if record['validated?'] and record not in project_data]
            weeks *= 3
        projects = []
        ids = list(set(ids))
        for project in project_data:
            if project['id'] in ids:
                projects.append(project)
                ids.remove(project['id'])
        return weeks_count, projects

    @cache(ttl=300)
    async def get_campus_locations(self, campus_id: int,
                                   time_zone: str) -> Tuple[float, List[Dict[str, Any]], List[Dict[str, Any]]]:
        endpoint = f'campus/{campus_id}/locations'

        now = datetime.now(timezone(time_zone))
        past = now - timedelta(hours=24)

        scan = datetime.now().timestamp()
        inactive = []
        page = 1
        params = {
            'sort': '-end_at',
            'filter[inactive]': 'true',
            'per_page': 100,
            'range[end_at]': f'{past},{now}',
            'page': page
        }
        data = await self._request(endpoint, params=params)
        while data and page <= 8:
            page += 1
            inactive.extend(data)
            params['page'] = page
            data = await self._request(endpoint, params=params)

        active = []
        page = 1
        params = {
            'filter[active]': 'true',
            'per_page': 100,
            'page': page
        }
        data = await self._request(endpoint, params=params)
        while data:
            page += 1
            active.extend(data)
            params['page'] = page
            data = await self._request(endpoint, params=params)
        return scan, active, inactive

    async def get_projects(self, cursus_id: int, project_names: List[str]) -> List[Dict[str, Any]]:
        endpoint = f'cursus/{cursus_id}/projects'
        projects = []
        start = 0
        stop = 100
        while start < 200:
            params = {
                'per_page': 100,
                'sort': 'name',
                'filter[name]': ','.join(project_names[start:stop])
            }
            data = await self._request(endpoint, params=params)
            for project in data:
                if project['name'] in project_names:
                    if project['parent']:
                        project['name'] = f"{project['parent']}: {project['name']}"
                    projects.append(project)
            start += 100
            stop += 100
        return projects
