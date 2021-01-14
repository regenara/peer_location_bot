from time import time

import aiohttp
from aiohttp.client_exceptions import ContentTypeError


class IntraRequests:
    def __init__(self, data: list):
        self.clients = {}
        self.data = data

    async def requests_get(self, url: str, args: dict = None) -> dict or list:
        if not self.clients:
            for key, client in enumerate(self.data):
                await self.get_token(key, client[0], client[1])
        key = min(self.clients.keys(), key=lambda key: self.clients[key]['last_call'])
        access_token = self.clients[key]['access_token']
        while True:
            params = {'access_token': access_token}
            if args is not None:
                params.update(args)
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as resp:
                        request = await resp.json()
                self.clients[key]['last_call'] = time()
                if isinstance(request, dict) and request.get('message') == 'The access token expired':
                    await self.get_token(key, self.clients[key]['client_id'], self.clients[key]['client_secret'])
                    access_token = self.clients[key]['access_token']
                    continue
            except ContentTypeError:
                continue
            break
        return request

    async def get_token(self, key: int, client_id: str, client_secret: str):
        url = 'https://api.intra.42.fr/oauth/token'
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params={'grant_type': 'client_credentials', 'client_id': client_id,
                                                 'client_secret': client_secret}) as resp:
                request = await resp.json()
        access_token = request['access_token']
        self.clients[key] = {'client_id': client_id, 'client_secret': client_secret,
                             'access_token': access_token, 'last_call': time()}

    async def get_user(self, nickname: str) -> dict:
        url = f'https://api.intra.42.fr/v2/users/{nickname}'
        info = await self.requests_get(url)
        return info

    async def get_user_coalition(self, nickname: str) -> str:
        url = f'https://api.intra.42.fr/v2/users/{nickname}/coalitions'
        coalitions = await self.requests_get(url)
        coalition = ''
        if coalitions:
            url = f'https://api.intra.42.fr/v2/users/{nickname}/coalitions_users'
            coalitions_users = await self.requests_get(url)
            coalition_id = coalitions_users[0]['coalition_id']
            coalition = [c['name'] for c in coalitions if c['id'] == coalition_id][0]
        return coalition

    async def get_last_locations(self, nickname: str) -> list:
        url = f'https://api.intra.42.fr/v2/users/{nickname}/locations'
        locations = await self.requests_get(url)
        return locations

    async def get_feedbacks(self, nickname: str, results_count: int) -> list:
        url = f'https://api.intra.42.fr/v2/users/{nickname}/scale_teams/as_corrector'
        feedbacks = await self.requests_get(url, {'per_page': results_count})
        return feedbacks

    async def get_project(self, project_id: int) -> dict:
        url = f'https://api.intra.42.fr/v2/projects/{project_id}'
        project = await self.requests_get(url)
        return project

    async def get_host(self, host: str) -> list:
        url = 'https://api.intra.42.fr/v2/locations'
        info = await self.requests_get(url, {'filter[host]': host})
        return info

    async def get_campuses(self) -> list:
        url = 'https://api.intra.42.fr/v2/campus'
        campuses = await self.requests_get(url, {'per_page': 100})
        return campuses
