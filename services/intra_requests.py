from io import BytesIO
from datetime import datetime
from datetime import timedelta
from pytz import timezone
from time import time
from typing import Any
from typing import Dict
from typing import List
from typing import Union
from urllib.parse import urljoin
import ssl

from aiohttp import ClientSession
from aiohttp import TCPConnector
from aiohttp.client_exceptions import ContentTypeError
from asyncio_throttle import Throttler
import certifi

from data.config import REDIRECT_URI


class IntraRequests:
    def __init__(self, data: list):
        """

        :param data: Список словарей [{'client_id': 'b26072d84a99...', 'client_secret': 'e2b6f5e33c...'}]
        """
        self.clients = {}
        self.data = data
        self.base_url = 'https://api.intra.42.fr/v2/'

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = TCPConnector(ssl=ssl_context)
        self.session: ClientSession = ClientSession(connector=connector)
        self.throttler = Throttler(rate_limit=10, period=1)

    async def request(self, endpoint: str, params: dict = None, access_token: str = None) -> Union[dict, list]:
        url = urljoin(self.base_url, endpoint)
        if not self.clients:
            for client_key, client in enumerate(self.data):
                await self.request_token(client_key, client['client_id'], client['client_secret'])
        client_key = min(self.clients.keys(), key=lambda key: self.clients[key]['last_call'])
        access_token = access_token or self.clients[client_key]['access_token']
        params = params or {}
        async with self.throttler:
            while True:
                params.update({'access_token': access_token})
                async with self.session.request('GET', url, params=params) as response:
                    self.clients[client_key]['last_call'] = time()
                    if response.status in (200, 201):
                        try:
                            js = await response.json()
                        except ContentTypeError:
                            continue
                        break
                    elif response.status == 401:
                        js = await response.json()
                        if js.get('message') == 'The access token expired':
                            await self.request_token(client_key, self.clients[client_key]['client_id'],
                                                     self.clients[client_key]['client_secret'])
                            access_token = self.clients[client_key]['access_token']
                            continue
                        return {'error': f'Intra response {response.status} {response.reason}'}
                    elif response.status == 429:
                        if endpoint == 'me':
                            continue
                        client_key = min(self.clients.keys(), key=lambda key: self.clients[key]['last_call'])
                        access_token = self.clients[client_key]['access_token']
                        continue
                    else:
                        return {'error': f'Intra response {response.status} {response.reason}'}
        return js

    async def request_token(self, client_key: int, client_id: str, client_secret: str,
                            grant_type: str = 'client_credentials', code: str = None) -> dict:
        """

        :param client_key: Ключ словаря
        :param client_id: client_id приложения Intra
        :param client_secret: client_secret приложения Intra
        :param grant_type:
        :param code:
        """
        url = 'https://api.intra.42.fr/oauth/token'
        params = {'grant_type': grant_type, 'client_id': client_id, 'client_secret': client_secret}
        if code:
            params.update({'code': code, 'redirect_uri': REDIRECT_URI})
        async with self.session.request('POST', url, params=params) as response:
            js = await response.json()
        if code:
            return js
        access_token = js['access_token']
        self.clients[client_key] = {'client_id': client_id, 'client_secret': client_secret,
                                    'access_token': access_token, 'last_call': time()}

    async def get_peer(self, nickname: str) -> dict:
        """

        :param nickname: Никнейм в Intra
        :return: Словарь с информацией о пользователе.
        Словарь с ошибкой и статусом, если Intra вернула ошибку
        """
        endpoint = f'users/{nickname}'
        return await self.request(endpoint)

    async def get_peers(self, nicknames: list) -> Union[List[dict], dict]:
        """

        :param nicknames: Список никнеймов в Intra
        :return: Список словарей с краткой информацией о пользователях.
        Пустой список, если пользователи не найдены.
        Словарь с ошибкой и статусом, если Intra вернула ошибку
        """
        endpoint = f'users'
        return await self.request(endpoint, params={'filter[login]': ','.join(nicknames)})

    async def get_peer_coalitions(self, nickname: str) -> Union[List[dict], dict]:
        """

        :param nickname: Никнейм в Intra
        :return: Список словарей с краткой информацией коалиций пользователя.
        Пустой список, если пользователь не состоит в коалиции.
        Словарь с ошибкой и статусом, если Intra вернула ошибку
        """
        endpoint = f'users/{nickname}/coalitions_users'
        return await self.request(endpoint)

    async def get_peer_locations(self, nickname: str) -> Union[List[dict], dict]:
        """

        :param nickname: Никнейм в Intra
        :return: Список словарей (максимум 50) с краткой информацией локаций пользователя.
        Пустой список, если пользователь не заходил в систему.
        Словарь с ошибкой и статусом, если Intra вернула ошибку
        """
        endpoint = f'users/{nickname}/locations'
        return await self.request(endpoint, params={'per_page': 50})

    async def get_peer_feedbacks(self, nickname: str) -> Union[List[dict], dict]:
        """

        :param nickname: Никнейм в Intra
        :return: Список словарей (максимум 50) с отзывами пользователя.
        Пустой список, если пользователь никого не оценивал.
        Словарь с ошибкой и статусом, если Intra вернула ошибку
        """
        endpoint = f'users/{nickname}/scale_teams/as_corrector'
        return await self.request(endpoint, params={'per_page': 50})

    async def get_coalition(self, coalition_id: int) -> dict:
        """

        :param coalition_id: ID коалиции
        :return: Словарь с информацией о коалиции.
        Словарь с ошибкой и статусом, если Intra вернула ошибку
        """
        endpoint = f'coalitions/{coalition_id}'
        return await self.request(endpoint)

    async def get_host(self, host: str) -> Union[List[dict], dict]:
        """

        :param host: Локация. Примеры: un-a1, ox-d4, er-f1
        :return: Список словарей (максимум 10) с краткой информацией о локации.
        Пустой список, если локация не найдена, возможно, также если еще никто не сидел на текущей локации.
        Словарь с ошибкой и статусом, если Intra вернула ошибку
        """
        endpoint = 'locations'
        return await self.request(endpoint, params={'filter[host]': host, 'per_page': 10})

    async def get_campus(self, campus_id: int) -> dict:
        """

        :param campus_id: ID кампуса
        :return: Словарь с информацией о кампусе.
        Словарь с ошибкой и статусом, если Intra вернула ошибку
        """
        endpoint = f'campus/{campus_id}'
        return await self.request(endpoint)

    async def get_project(self, project_id: int) -> dict:
        """

        :param project_id: ID проекта
        :return: Словарь с информацией о проекте.
        Словарь с ошибкой и статусом, если Intra вернула ошибку
        """
        endpoint = f'projects/{project_id}'
        return await self.request(endpoint)

    async def get_project_peers(self, project_id: int, campus_id: int, time_zone: str) -> Dict[str, Any]:
        """

        :param project_id: ID проекта
        :param campus_id: ID кампуса
        :param time_zone: Часовой пояс кампуса
        :return: Словарь со списком пользователей (максимум 50), выполнивших проект за последние 4 недели.
        Если пользователей менее 30, то количество недель увеличивается в три раза до тех пор,
        пока список не будет содержать минимум 30 пользователей или количество недель не перевалит за 36.
        Также в словаре указано количество недель и ошибка, если если Intra вернула таковую
        """
        endpoint = f'projects/{project_id}/projects_users'
        data = []
        weeks = 4
        result = {}
        while len(data) < 30 and weeks < 37:
            result.update({'weeks': weeks})
            now = datetime.now(timezone(time_zone))
            past = now - timedelta(weeks=weeks)
            all_data = await self.request(endpoint, params={'filter[campus]': campus_id,
                                                            'per_page': 100,
                                                            'range[marked_at]': f'{past},{now}',
                                                            'range[final_mark]': '80,150'})
            if isinstance(all_data, dict) and all_data.get('error'):
                result.update({'error': all_data['error']})
                break
            data = [record for record in all_data if record['validated?']]
            weeks *= 3
        result.update({'data': data})
        return result

    async def get_campus_locations(self, campus_id: int, past: str, now: str, pages: int) -> Dict[str, Any]:
        """

        :param campus_id: ID кампуса
        :param past: Время с
        :param now: Время по
        :param pages: Максимальное количество загружаемых страниц
        :return: Словарь с двумя списками - с активными и неактивными локациями. Все активные на данные момент
        и список неактивных за последнее время. Данные необходимо отсортировать, ибо в неактивных будут повторяться
        локации, также локация могла быть полчаса неактивной, но сейчас она занята, однако запись в неактивных
        все равно будет. Также в словаре указана ошибка, если если Intra вернула таковую
        """
        endpoint = f'campus/{campus_id}/locations'
        result = {}
        inactive_data = []
        active_data = []
        page = 1
        inactive = await self.request(endpoint, params={'sort': '-end_at', 'filter[inactive]': 'true', 'per_page': 100,
                                                        'range[end_at]': f'{past},{now}', 'page': page})
        while inactive and page <= pages:
            page += 1
            if isinstance(inactive, dict) and inactive.get('error'):
                result.update({'error': inactive['error']})
                break
            inactive_data.extend(inactive)
            inactive = await self.request(endpoint,
                                          params={'sort': '-end_at', 'filter[inactive]': 'true', 'per_page': 100,
                                                  'range[end_at]': f'{past},{now}', 'page': page})
        page = 1
        active = await self.request(endpoint, params={'filter[active]': 'true', 'per_page': 100, 'page': page})
        while active:
            page += 1
            if isinstance(active, dict) and active.get('error'):
                result.update({'error': active['error']})
                break
            active_data.extend(active)
            active = await self.request(endpoint, params={'filter[active]': 'true', 'per_page': 100, 'page': page})
        result.update({'active': active_data, 'inactive': inactive_data})
        return result

    async def update_projects(self, file: BytesIO, cursus_id: int = 21):
        """

        :param file: Файл html страницы проектов https://projects.intra.42.fr/projects/list
        :param cursus_id: ID курса, по умолчанию 21 == 42cursus
        """
        from bs4 import BeautifulSoup
        import misc

        text = file.read().decode('utf-8')
        soup = BeautifulSoup(text, 'lxml')
        list_projects = [project.text.strip() for project in soup.find_all('div', class_='project-name')]

        endpoint = f'cursus/{cursus_id}/projects'
        projects = []
        start = 0
        stop = 100
        while start < 200:
            data = await self.request(endpoint, params={'per_page': 100, 'sort': 'id',
                                                        'filter[name]': ','.join(list_projects[start:stop])})
            for project in data:
                if project['name'] in list_projects:
                    projects.append({'name': project['name'], 'project_id': project['id'], 'slug': project['slug']})
            start += 100
            stop += 100
        await misc.mongo.delete_all('projects42')
        await misc.mongo.insert_many('projects42', projects)
