from datetime import datetime
from datetime import timedelta
from pytz import timezone
from time import time
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
        :param state:
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

    async def get_project_peers(self, project_id: int, campus_id: int, time_zone: str):
        """

        :param project_id: ID проекта
        :param campus_id: ID кампуса
        :param time_zone: Часовой пояс кампуса
        :return: Словарь со списком пользователей (максимум 50), выполнивших проект за последние 4 недели.
        Если пользователей менее 30, то количество недель увеличивается в три раза до тех пор,
        пока список не будет содержать минимум 30 пользователей или количество недель не перевалит 36.
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
            data = await self.request(endpoint, params={'filter[campus]': campus_id, 'per_page': 50,
                                                        'range[marked_at]': f'{past},{now}',
                                                        'range[final_mark]': '100,150'})
            if isinstance(data, dict) and data.get('error'):
                result.update({'error': data['error']})
                break
            weeks *= 3
        result.update({'data': data})
        return result

    async def get_projects(self, cursus_id: int = 21):
        """

        :param cursus_id: ID курса, по умолчанию 21 == 42cursus
        :return: Список (ниже) из 129 проектов (без бассейнов и стажировок)
        """
        endpoint = f'cursus/{cursus_id}/projects'
        projects = []
        list_projects = ['Libft', 'ft_printf', 'netwhat', 'get_next_line', 'ft_server', 'miniRT', 'cub3d',
                         'ft_services', 'libasm', 'minishell', 'webserv', 'Philosophers', 'ft_containers',
                         'ft_irc', 'ft_transcendence', 'ft_hangouts', 'taskmaster', 'computorv1', 'gomoku',
                         'expert-system', 'n-puzzle', 'nibbler', '42run', 'strace', 'bomberman', 'scop',
                         'ft_linear_regression', 'krpsim', 'rubik', 'humangl', 'swifty-companion', 'camagru',
                         'ft_ping', 'ft_traceroute', 'ft_nmap', 'matcha', 'hypertube', 'ft_turing', 'snow-crash',
                         'darkly', 'swifty-proteins', 'ft_ality', 'xv', 'in-the-shadows', 'particle-system', 'gbmu',
                         'cloud-1', 'ft_linux', 'little-penguin-1', 'rainfall', 'dr-quine', 'woody-woodpacker',
                         'matt-daemon', 'process-and-memory', 'drivers-and-interrupts', 'filesystem', 'kfs-2',
                         'kfs-1', 'kfs-3', 'music-room', 'red-tetris', 'h42n42', 'famine', 'kfs-4', 'kfs-5',
                         'computorv2', 'avaj-launcher', 'swingy', 'fix-me', 'kfs-6', 'kfs-7', 'kfs-8', 'kfs-9',
                         'kfs-x', 'pestilence', 'war', 'death', 'boot2root', 'durex', 'override', 'ft_vox',
                         'ft_ssl_rsa', 'ft_ssl_md5', 'ft_ssl_des', 'dslr', 'shaderpixel', 'guimp',
                         'userspace_digressions', 'multilayer-perceptron', 'total-perspective-vortex', 'abstract-vm',
                         'mod1', 'zappy', 'lem-ipc', 'ft_script', 'nm-otool', 'malloc', 'ft_select', 'lem_in',
                         'push_swap', 'corewar', 'fract-ol', 'ft_ls', 'CPP Module 00', 'CPP Module 01', 'CPP Module 02',
                         'CPP Module 03', 'CPP Module 04', 'CPP Module 05', 'CPP Module 06', 'CPP Module 07',
                         'CPP Module 08', 'Electronics-Old', 'Old-LibftASM', 'Old-Philosophers', 'Old-IRC',
                         'Old-CPP Module 00', 'Old-CPP Module 01', 'Old-CPP Module 02', 'Old-CPP Module 03',
                         'Old-CPP Module 04', 'Old-CPP Module 05', 'Old-CPP Module 06', 'Old-CPP Module 07',
                         'Old-CPP Module 08', '42 Squads', 'darkly - web', 'ft_malcolm', 'Electronique']

        start = 0
        stop = 100
        while start < 200:
            data = await self.request(endpoint, params={'per_page': 100, 'filter[exam]': 'false', 'sort': 'id',
                                                        'filter[name]': ','.join(list_projects[start:stop])})
            for project in data:
                if project['name'] in list_projects:
                    projects.append({'name': project['name'], 'project_id': project['id'], 'slug': project['slug']})
            start += 100
            stop += 100
        return projects

    async def get_campus_locations(self, campus_id: int, past: str, now: str, pages: int):
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
