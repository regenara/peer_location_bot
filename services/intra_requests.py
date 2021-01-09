from time import time
from json.decoder import JSONDecodeError

import requests


class IntraRequests:
    def __init__(self, clients: list):
        self.clients = {}
        for key, client in enumerate(clients):
            self.get_token(key, client[0], client[1])

    def requests_get(self, url: str, args: dict = None) -> dict or list:
        key = min(self.clients.keys(), key=lambda key: self.clients[key]['last_call'])
        access_token = self.clients[key]['access_token']
        while True:
            params = {'access_token': access_token}
            if args is not None:
                params.update(args)
            try:
                request = requests.get(url, params=params).json()
                self.clients[key]['last_call'] = time()
                if isinstance(request, dict) and request.get('message') == 'The access token expired':
                    self.get_token(key, self.clients[key]['client_id'], self.clients[key]['client_secret'])
                    access_token = self.clients[key]['access_token']
                    continue
            except JSONDecodeError:
                continue
            break
        return request

    def get_token(self, key: int, client_id: str, client_secret: str):
        url = 'https://api.intra.42.fr/oauth/token'
        request = requests.post(url, params={'grant_type': 'client_credentials', 'client_id': client_id,
                                             'client_secret': client_secret}).json()
        access_token = request['access_token']
        self.clients[key] = {'client_id': client_id, 'client_secret': client_secret,
                             'access_token': access_token, 'last_call': time()}

    def get_user(self, nickname: str) -> dict:
        url = f'https://api.intra.42.fr/v2/users/{nickname}'
        info = self.requests_get(url)
        return info

    def get_user_coalition(self, nickname: str) -> str:
        url = f'https://api.intra.42.fr/v2/users/{nickname}/coalitions'
        coalitions = self.requests_get(url)
        coalition = ''
        if coalitions:
            url = f'https://api.intra.42.fr/v2/users/{nickname}/coalitions_users'
            coalitions_users = self.requests_get(url)
            coalition_id = coalitions_users[0]['coalition_id']
            coalition = [c['name'] for c in coalitions if c['id'] == coalition_id][0]
        return coalition

    def get_last_locations(self, nickname: str) -> list:
        url = f'https://api.intra.42.fr/v2/users/{nickname}/locations'
        locations = self.requests_get(url)
        return locations

    def get_feedbacks(self, nickname: str, results_count: int) -> list:
        url = f'https://api.intra.42.fr/v2/users/{nickname}/scale_teams/as_corrector'
        feedbacks = self.requests_get(url, {'per_page': results_count})
        return feedbacks

    def get_project(self, project_id: int) -> dict:
        url = f'https://api.intra.42.fr/v2/projects/{project_id}'
        project = self.requests_get(url)
        return project

    def get_host(self, host: str) -> list:
        url = 'https://api.intra.42.fr/v2/locations'
        info = self.requests_get(url, {'filter[host]': host})
        return info

    def get_campuses(self) -> list:
        url = 'https://api.intra.42.fr/v2/campus'
        campuses = self.requests_get(url, {'per_page': 100})
        return campuses
