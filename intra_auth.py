import requests

from utils import read_json

data = read_json('data.json')
client_id = data['client_id']
client_secret = data['client_secret']


def get_token():
    request = requests.post('https://api.intra.42.fr/oauth/token', params={'grant_type': 'client_credentials',
                                                                           'client_id': client_id,
                                                                           'client_secret': client_secret})
    access_token = request.json()['access_token']
    return access_token


def get_user(nickname, access_token):
    url = f'https://api.intra.42.fr/v2/users/{nickname}'
    info = requests.get(url, params={'access_token': access_token}).json()
    return info
