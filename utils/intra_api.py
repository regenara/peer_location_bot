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


class IntraAPI:
    def __init__(self, config, test: bool = False):
        self._apps: Deque = deque()
        self._base_url = 'https://api.intra.42.fr/v2/'
        self._auth_url = 'https://api.intra.42.fr/oauth/token'
        self._config = config
        self._test = test
        self._refresher = None
        self._logger = logging.getLogger('IntraAPI')

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = TCPConnector(ssl=ssl_context)
        self.session: ClientSession = ClientSession(connector=connector, json_serialize=ujson.dumps)
        self._throttler = Throttler(rate_limit=24)

    async def _tokens_refresher(self):
        while True:
            sleep = 5
            if not datetime.now().minute:
                self._logger.info('Starting refresh tokens')
                await self.load()
                self._logger.info('Complete refresh tokens, sleep 120 seconds')
                sleep = 120
            await asyncio.sleep(sleep)

    @property
    def _get_token(self) -> int:
        access_token = self._apps[0]
        self._apps.rotate(1)
        return access_token

    async def _request_token(self, params: Dict[str, str]) -> str:
        async with self.session.request('POST', self._auth_url, params=params) as response:
            if response.status == 200:
                js = await response.json()
                return js['access_token']

    async def _request(self, endpoint: str, params: dict = None, headers: dict = None) -> Union[Dict[str, Any],
                                                                                                List[Dict[str, Any]]]:
        url = urljoin(self._base_url, endpoint)
        params = params or {}
        access_token = self._get_token
        async with self._throttler:
            attempts = 1
            while attempts < 11:
                headers = headers or {'Authorization': f'Bearer {access_token}'}
                async with self.session.request('GET', url, params=params, headers=headers) as response:
                    if response.status == 200:
                        try:
                            json_response = await response.json()
                            self._logger.info('Response with token=%s url=%s', access_token, url)
                            return json_response
                        except ContentTypeError as e:
                            self._logger.error('Response url=%s: ContentTypeError %s, continue', url, e)
                            continue

                    attempts += 1
                    if response.status in (401, 429) and endpoint != 'me':
                        self._logger.error('Response %s with token=%s url=%s: %s [%s], continue',
                                           attempts, access_token, url, response.reason, response.status)
                        access_token = self._get_token
                        continue

                    if response.status == 404:
                        self._logger.error('Response url=%s: %s [%s], raise NotFoundIntraError',
                                           url, response.reason, response.status)
                        raise NotFoundIntraError(f'Intra response: {response.reason} [{response.status}]')

                    self._logger.error('Response %s token=%s url=%s: %s [%s]',
                                       attempts, access_token, url, response.reason, response.status)

        self._logger.error('Response %s url=%s: %s [%s], raise UnknownIntraError',
                           attempts, url, response.reason, response.status)
        raise UnknownIntraError(f'Intra response: {response.reason} [{response.status}]')

    async def start(self):
        self._refresher = asyncio.create_task(self._tokens_refresher())

    async def stop(self):
        self._refresher.cancel()

    async def load(self):
        applications = await Application.get_all() if not self._test else [await Application.get_test()]
        self._apps = deque(maxlen=len(applications))
        for application in applications:
            params = {
                'grant_type': 'client_credentials',
                'client_id': application.client_id,
                'client_secret': application.client_secret
            }
            access_token = await self._request_token(params=params)
            self._apps.append(access_token)
            self._logger.info('Get token=%s from application=%s', access_token, application.id)

    async def auth(self, client_id: str, client_secret: str, code: str) -> str:
        params = {
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': self._config.redirect_uri
        }
        return await self._request_token(params=params)

    async def get_me(self, headers: Dict[str, Any]) -> Dict[str, Any]:
        endpoint = 'me'
        return await self._request(endpoint, headers=headers)

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
    async def get_peer_locations(self, login: str) -> List[Dict[str, Any]]:
        endpoint = f'users/{login}/locations'
        return await self._request(endpoint, params={'per_page': 50})

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

    @cache(ttl=3600)
    async def get_project_peers(self, project_id: int, campus_id: int,
                                time_zone: str) -> Tuple[int, List[Dict[str, Any]]]:
        endpoint = f'projects/{project_id}/projects_users'
        project_data = []
        weeks = 4
        weeks_count = weeks
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
            project_data = [record for record in data if record['validated?']]
            weeks *= 3
        return weeks_count, project_data

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
                    projects.append(project)
            start += 100
            stop += 100
        return projects
