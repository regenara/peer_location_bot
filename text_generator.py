from datetime import datetime, timezone
from time import mktime

import intra_requests
from localization import get_user_info


def text_compile(message_text: str, lang: str, avatar: bool) -> str:
    get_nicknames = message_text.lower().split()
    nicknames = list(dict.fromkeys(get_nicknames))[:5]
    user_info_localization = get_user_info(lang)
    texts = []
    for nickname in nicknames:
        info = {}
        if 1 < len(nickname) < 20 and '.' not in nickname and '/' not in nickname and '\\' not in nickname \
                and '#' not in nickname and '%' not in nickname:
            access_token = intra_requests.get_token()
            info = intra_requests.get_user(nickname, access_token)
        elif len(nickname) > 20:
            nickname = f'{nickname[:20]}...'
        text = eval(user_info_localization['not_found'])
        if info:
            user_id = info['id']
            coalition = intra_requests.get_user_coalition(user_id, access_token)
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
                location = last_location_info(user_id, access_token, user_info_localization)
            text = f'<b>{displayname}</b> aka {login}\n<b>{user_info_localization["coalition"]}:</b> {coalition}\n' \
                   f'{cursus_info}\n<b>{user_info_localization["campus"]}:</b> {campus}\n' \
                   f'<b>{user_info_localization["location"]}:</b> {location}'
            if avatar and image_url:
                text += f'<a href="{image_url}">​</a>'
        texts.append(text)
    return f'\n➖➖➖➖➖➖➖➖➖➖\n'.join(texts)


def last_location_info(user_id: int, access_token: str, user_info_localization: dict) -> str:
    get_last_location_info = intra_requests.get_last_locations(user_id, access_token)[0]
    last_location_end = get_last_location_info['end_at'].replace('Z', '+00:00')
    date = datetime.fromisoformat(last_location_end)
    now = datetime.now(timezone.utc)
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
