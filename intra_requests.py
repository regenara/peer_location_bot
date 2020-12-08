import requests
from json.decoder import JSONDecodeError


class IntraRequests:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    def requests_get(self, url: str, access_token: str) -> dict or list:
        while True:
            try:
                request = requests.get(url, params={'access_token': access_token}).json()
                if isinstance(request, dict) and request.get('message') == 'The access token expired':
                    access_token = self.get_token()
                    continue
            except JSONDecodeError:
                continue
            break
        return request

    def get_token(self) -> str:
        url = 'https://api.intra.42.fr/oauth/token'
        request = requests.post(url, params={'grant_type': 'client_credentials', 'client_id': self.client_id,
                                             'client_secret': self.client_secret}).json()
        access_token = request['access_token']
        return access_token

    def get_user(self, nickname: str, access_token: str) -> dict:
        url = f'https://api.intra.42.fr/v2/users/{nickname}'
        info = self.requests_get(url, access_token)
        return info

    def get_user_coalition(self, user_id: int, access_token: str) -> str:
        url = f'https://api.intra.42.fr/v2/users/{user_id}/coalitions_users'
        coalition_id = self.requests_get(url, access_token)[0]['coalition_id']
        url = 'https://api.intra.42.fr/v2/coalitions'
        get_coalitions = self.requests_get(url, access_token)
        coalition = [c['name'] for c in get_coalitions if c['id'] == coalition_id][0]
        return coalition

    def get_last_locations(self, user_id: int, access_token: str) -> list:
        url = f'https://api.intra.42.fr/v2/users/{user_id}/locations'
        locations = self.requests_get(url, access_token)
        return locations

    def get_campuses(self, access_token: str) -> list:
        url = 'https://api.intra.42.fr/v2/campus'
        campuses = self.requests_get(url, access_token)
        return campuses
