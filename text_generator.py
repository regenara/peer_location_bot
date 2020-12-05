from datetime import datetime, timezone
from time import mktime

import intra_requests


def text_compile(message_text: str) -> str:
    nicknames = message_text.lower().replace('@', '').split()
    texts = []
    for nickname in list(dict.fromkeys(nicknames))[:5]:
        if len(nickname) < 40:
            access_token = intra_requests.get_token()
            info = intra_requests.get_user(nickname, access_token)
        else:
            nickname = f'{nickname[:40]}...'
            info = {}
        text = f'Пользователь <b>{nickname}</b> не найден! Проверь правильность введенных данных'
        if info:
            user_id = info['id']
            coalition = intra_requests.get_user_coalition(user_id, access_token)
            displayname = info['displayname']
            login = info['login']
            cursus_users = info['cursus_users']
            cursus_info = '\n'.join([f'<b>{c["cursus"]["name"]}:</b> {round(c["level"], 2)}' for c in cursus_users])
            get_primary_campus_id = [campus['campus_id'] for campus in info['campus_users'] if campus['is_primary']][0]
            campus = [campus['name'] for campus in info['campus'] if campus['id'] == get_primary_campus_id][0]
            image_url = info['image_url']
            location = info['location']
            if info['staff?']:
                location = 'Спроси в АДМ'
            if location is None:
                location = last_location_info(user_id, access_token)
            text = f'<b>{displayname}</b> aka {login}\n<b>Коалиция:</b> {coalition}\n{cursus_info}\n<b>Кампус:</b> ' \
                   f'{campus}\n<b>Место:</b> {location}'
        texts.append(text)
    return f'\n➖➖➖➖➖➖➖➖➖➖\n'.join(texts)


def last_location_info(user_id: int, access_token: str) -> str:
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
        days_gone = f'{days}д '
    if hours:
        hours_gone = f'{hours}ч '
    if minutes:
        minutes_gone = f'{str(minutes).zfill(2)}м '
    return f'Не в кампусе. Последняя активность <b>{days_gone}{hours_gone}{minutes_gone}</b>назад'
