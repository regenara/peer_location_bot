import requests

from utils import read_json

data = read_json('data.json')
client_id = data['client_id']
client_secret = data['client_secret']


def requests_get(url: str, access_token: str) -> dict or list:
    while True:
        try:
            request = requests.get(url, params={'access_token': access_token}).json()
        except:
            continue
        break
    return request


def get_token() -> str:
    url = 'https://api.intra.42.fr/oauth/token'
    request = requests.post(url, params={'grant_type': 'client_credentials', 'client_id': client_id,
                                         'client_secret': client_secret}).json()
    access_token = request['access_token']
    return access_token


def get_user(nickname: str, access_token: str) -> dict:
    url = f'https://api.intra.42.fr/v2/users/{nickname}'
    info = requests_get(url, access_token)
    return info


def get_user_coalition(user_id: int, access_token: str) -> str:
    url = f'https://api.intra.42.fr/v2/users/{user_id}/coalitions_users'
    coalition_id = requests_get(url, access_token)[0]['coalition_id']
    url = 'https://api.intra.42.fr/v2/coalitions'
    get_coalitions = requests_get(url, access_token)
    coalition = [c['name'] for c in get_coalitions if c['id'] == coalition_id][0]
    return coalition


def get_last_locations(user_id: int, access_token: str) -> list:
    url = f'https://api.intra.42.fr/v2/users/{user_id}/locations'
    locations = requests_get(url, access_token)
    return locations


t = get_token()
#print(t)
u = get_user('mspyke', t)
#print(get_last_locations(u['id'], t))

"""id_ = u['id']
last_location_info = get_last_locations(id_, t)[0]
last_location = last_location_info['host']
last_location_end = last_location_info['end_at'].replace('Z', '+00:00')
date = datetime.fromisoformat(last_location_end)
now = datetime.now(timezone.utc)
seconds = mktime(now.timetuple()) - mktime(date.timetuple())
seconds_in_day = 60 * 60 * 24
seconds_in_hour = 60 * 60
seconds_in_minute = 60

days = int(seconds // seconds_in_day)
hours = int((seconds - (days * seconds_in_day)) // seconds_in_hour)
minutes = int((seconds - (days * seconds_in_day) - (hours * seconds_in_hour)) // seconds_in_minute)
print(days, hours, minutes)
print(last_location_info)
"""