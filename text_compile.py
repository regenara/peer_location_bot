from datetime import datetime
from pytz import timezone
from time import mktime

from config import localization_texts
from config import client_id
from config import client_secret
from intra_requests import IntraRequests
from utils import nickname_check


intra = IntraRequests(client_id, client_secret)


def get_users_info(message_text: str, lang: str, avatar: bool, friends: dict) -> dict:
    get_nicknames = message_text.lower().split()
    nicknames = list(dict.fromkeys(get_nicknames))[:5]
    user_info_localization = localization_texts['user_info'][lang]
    texts = []
    intra_users = []
    for nickname in nicknames:
        nickname_valid = nickname_check(nickname)
        info = {}
        if nickname_valid:
            access_token = intra.get_token()
            info = intra.get_user(nickname, access_token)
        elif len(nickname) > 20:
            nickname = f'{nickname[:20]}...'
        text = eval(user_info_localization['not_found'])
        if info:
            intra_user_id = info['id']
            coalition = intra.get_user_coalition(intra_user_id, access_token)
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
            key = 'friend'
            if login not in friends:
                key = 'not_friend'
            text = f'<b>{displayname}</b> aka {login}\n<b>{user_info_localization[key]}</b>\n<b>' \
                   f'{user_info_localization["coalition"]}:</b> {coalition}\n{cursus_info}\n<b>' \
                   f'{user_info_localization["campus"]}:</b> {campus}\n<b>{user_info_localization["location"]}:</b> ' \
                   f'{location}'
            if avatar and image_url:
                text += f'<a href="{image_url}">​</a>'
            intra_users.append(login)
        texts.append(text)
    data = {'text': f'\n\n'.join(texts), 'intra_users': intra_users}
    return data


def get_last_seen_time(intra_user_id: int, access_token: str, user_info_localization: dict) -> str:
    last_location_info = intra.get_last_locations(intra_user_id, access_token)[0]
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
    last_location_localization = localization_texts['last_locations']
    local_time = last_location_localization[lang]['local_time']
    nickname_valid = nickname_check(nickname)
    if not nickname_valid:
        return eval(user_info_localization['not_found'])
    access_token = intra.get_token()
    info = intra.get_user(nickname, access_token)
    intra_user_id = info['id']
    displayname = info['displayname']
    login = info['login']
    last_locations = intra.get_last_locations(intra_user_id, access_token)
    campuses = intra.get_campuses(access_token)
    head = f'<b>{displayname}</b> aka {login}'
    texts = []
    for location in last_locations:
        campus = [(campus['name'], campus['time_zone']) for campus in campuses
                  if campus['id'] == location['campus_id']][0]
        begin_at = location['begin_at'].replace('Z', '+00:00')
        log_in_time = datetime.fromisoformat(begin_at).astimezone(timezone(campus[1])).strftime('%H:%M  %d.%m.%y')
        log_out_time = last_location_localization[lang]['now']
        if location['end_at'] is not None:
            end_at = location['end_at'].replace('Z', '+00:00')
            log_out_time = datetime.fromisoformat(end_at).astimezone(timezone(campus[1])).strftime('%H:%M  %d.%m.%y')
        log_time = f'{log_in_time} - {log_out_time}'
        if log_in_time[7:] == log_out_time[7:]:
            log_time = f'{log_in_time[:5]} - {log_out_time[:5]}  {log_in_time[7:]}'
        text = f'<b>{campus[0]} {location["host"]}</b>\n{log_time}'
        texts.append(text)
    if texts:
        texts.insert(0, f'<i>{local_time}</i>')
    else:
        texts = [last_location_localization[lang]['not_logged']]
    return f'{head}\n' + f'\n'.join(texts)
