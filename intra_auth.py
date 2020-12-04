import requests

from utils import read_json

data = read_json('data.json')
client_id = data['client_id']
client_secret = data['client_secret']


def requests_get(url, access_token):
     request = requests.get(url, params={'access_token': access_token}).json()
     return request


def get_token():
    request = requests.post('https://api.intra.42.fr/oauth/token', params={'grant_type': 'client_credentials',
                                                                           'client_id': client_id,
                                                                           'client_secret': client_secret})
    access_token = request.json()['access_token']
    return access_token


def get_user(nickname, access_token):
    url = f'https://api.intra.42.fr/v2/users/{nickname}'
    info = requests_get(url, access_token)
    return info


def get_user_coalition(user_id, access_token):
    url = f'https://api.intra.42.fr/v2/users/{user_id}/coalitions_users'
    coalition_id = requests_get(url, access_token)[0]['coalition_id']
    url = 'https://api.intra.42.fr/v2/coalitions'
    get_coalitions = requests_get(url, access_token)
    coalition = [c['name'] for c in get_coalitions if c['id'] == coalition_id][0]
    return coalition


def get_last_locations(user_id, access_token):
    url = f'https://api.intra.42.fr/v2/users/{user_id}/location'
    locations = requests_get(url, access_token)[0]
    print(locations)


t = get_token()
print(3)
id_ = get_user('mstoneho', t)['id']
print(2)
get_last_locations(id_, t)
print(1)
