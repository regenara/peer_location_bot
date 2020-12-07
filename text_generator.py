from datetime import datetime
from pytz import timezone
from time import mktime, gmtime

import intra_requests
from config import localization_texts
from utils import nickname_check


def text_compile(message_text: str, lang: str, avatar: bool) -> dict:
    get_nicknames = message_text.lower().split()
    nicknames = list(dict.fromkeys(get_nicknames))[:5]
    user_info_localization = localization_texts['user_info'][lang]
    texts = []
    users = []
    for nickname in nicknames:
        nickname_valid = nickname_check(nickname)
        info = {}
        if nickname_valid:
            access_token = intra_requests.get_token()
            info = intra_requests.get_user(nickname, access_token)
        elif len(nickname) > 20:
            nickname = f'{nickname[:20]}...'
        text = eval(user_info_localization['not_found'])
        if info:
            intra_user_id = info['id']
            coalition = intra_requests.get_user_coalition(intra_user_id, access_token)
            displayname = info['displayname']
            login = info['login']
            cursus_users = info['cursus_users']
            cursus_info = '\n'.join([f'<b>{c["cursus"]["name"]}:</b> {round(c["level"], 2)}' for c in cursus_users])
            primary_campus_id = [campus['campus_id'] for campus in info['campus_users'] if campus['is_primary']][0]
            campus = [campus['name'] for campus in info['campus'] if campus['id'] == primary_campus_id][0]
            image_url = ''
            if len(nicknames) < 2:
                image_url = info['image_url']
            location = info['location']
            if info['staff?']:
                location = user_info_localization['ask_adm']
            if location is None:
                location = get_last_seen_time(intra_user_id, access_token, user_info_localization)
            text = f'<b>{displayname}</b> aka {login}\n<b>{user_info_localization["coalition"]}:</b> {coalition}\n' \
                   f'{cursus_info}\n<b>{user_info_localization["campus"]}:</b> {campus}\n' \
                   f'<b>{user_info_localization["location"]}:</b> {location}'
            if avatar and image_url:
                text += f'<a href="{image_url}">​</a>'
            users.append(login)
        texts.append(text)
    data = {'text': f'\n➖➖➖➖➖➖➖➖➖➖\n'.join(texts), 'users': users}
    return data


def get_last_seen_time(intra_user_id: int, access_token: str, user_info_localization: dict) -> str:
    last_location_info = intra_requests.get_last_locations(intra_user_id, access_token)[0]
    last_location_end = last_location_info['end_at'].replace('Z', '+00:00')
    date = datetime.fromisoformat(last_location_end)
    now = datetime.now(timezone('UTC'))
    seconds = mktime(now.timetuple()) - mktime(date.timetuple())
    seconds_in_day = 60 * 60 * 24
    seconds_in_hour = 60 * 60
    seconds_in_minute = 60
    days = int(seconds // seconds_in_day)
    hours = int((seconds - (days * seconds_in_day)) // seconds_in_hour)
    minutes = int((seconds - (days * seconds_in_day) - (hours * seconds_in_hour)) // seconds_in_minute)
    days_gone = ''
    hours_gone = ''
    minutes_gone = ''
    if days:
        days_gone = f'{days}{user_info_localization["days"]} '
    if hours:
        hours_gone = f'{hours}{user_info_localization["hours"]} '
    if minutes:
        minutes_gone = f'{str(minutes).zfill(2)}{user_info_localization["minutes"]} '
    return eval(user_info_localization['not_on_campus'])


def get_last_locations(nickname: str, lang: str) -> str:
    user_info_localization = localization_texts['user_info'][lang]
    nickname_valid = nickname_check(nickname)
    if not nickname_valid:
        return eval(user_info_localization['not_found'])
    access_token = intra_requests.get_token()
    info = intra_requests.get_user(nickname, access_token)
    intra_user_id = info['id']
    last_locations = intra_requests.get_last_locations(intra_user_id, access_token)
    campuses = intra_requests.get_campuses(access_token)
    texts = []
    for location in last_locations:
        campus = [(campus['name'], campus['time_zone']) for campus in campuses
                  if campus['id'] == location['campus_id']][0]
        begin_at = location['begin_at'].replace('Z', '+00:00')
        begin_at_unix_time = mktime(datetime.fromisoformat(begin_at).timetuple())
        log_in_time = datetime.fromtimestamp(begin_at_unix_time, timezone(campus[1])).strftime('%H:%M:%S %d.%m.%Y')
        log_out_time = ''
        if location['end_at'] is not None:
            end_at = location['end_at'].replace('Z', '+00:00')
            end_at_unix_time = mktime(datetime.fromisoformat(end_at).timetuple())
            print(end_at_unix_time)
            log_out_time = datetime.fromtimestamp(end_at_unix_time, timezone(campus[1])).strftime('%H:%M:%S %d.%m.%Y')
            log_out_time = f'\nLog out: {log_out_time}'
        text = f'{user_info_localization["campus"]}: {campus[0]}\n' \
               f'{user_info_localization["location"]}: {location["host"]}\n' \
               f'Log in: {log_in_time}{log_out_time}'
        texts.append(text)
    return f'\n➖➖➖➖➖➖➖➖➖➖\n'.join(texts)

