from datetime import datetime
from datetime import timedelta
from pytz import timezone
from typing import Any
from typing import Dict

from aiogram.utils.markdown import hide_link
from aiogram.utils.parts import paginate

from misc import intra_requests
from misc import mongo
from models.feedback import Feedback
from models.host import Host
from models.peer import Peer
from utils.helpers import get_data_from_message
from utils.helpers import get_log_time
from utils.helpers import get_peer_title
from utils.helpers import get_str_time
from utils.helpers import get_utc


async def peer_data_compile(nickname: str, peer_data_locale: dict,
                            is_alone: bool, avatar: bool = False) -> Dict[str, Any]:
    peer_data = await intra_requests.get_peer(nickname)
    if peer_data.get('error') and '404' in peer_data['error']:
        return {'text': peer_data_locale['not_found'].format(nickname=nickname.replace("<", "&lt")),
                'error': True}
    if peer_data.get('error'):
        return {'text': f'<b>{nickname}</b>: {peer_data["error"]}', 'error': True}
    peer = await Peer.from_dict(peer_data)
    cursus = '\n'.join([f'<b>{c["cursus"]["name"]}:</b> {round(c["level"], 2)}' for c in peer.cursus_data])
    coalition = ''
    if peer.coalition:
        coalition = f'<b>{peer_data_locale["coalition"]}:</b> {peer.coalition}\n'
    pool = ''
    if peer.pool:
        pool = f'<b>{peer_data_locale["piscine"]}:</b> {peer.pool}\n'
    if peer.is_staff:
        peer.location = peer_data_locale['ask_adm']
    if not peer.location:
        peer.location = last_seen_time_compile(peer.last_seen_time, peer.last_location, peer_data_locale)
    elif peer.location != peer_data_locale['ask_adm']:
        peer.location = f'<code>{peer.location}</code>'
    full_name = f'<b>{peer.full_name}</b>'
    if is_alone:
        full_name = f'<a href="{peer.link}">{peer.full_name}</a>'
    username = ''
    if peer.username:
        username = f'<b>Telegram:</b> @{peer.username}\n'
    text = f'{peer.status}{full_name} aka <code>{peer.nickname}</code>\n' \
           f'{username}' \
           f'{pool}' \
           f'{coalition}' \
           f'{cursus}\n' \
           f'<b>{peer_data_locale["campus"]}:</b> {peer.campus}\n' \
           f'<b>{peer_data_locale["location"]}:</b> {peer.location}'
    if avatar and is_alone:
        text = hide_link(peer.avatar) + text
    return {'text': text}


def last_seen_time_compile(last_seen_time: float, last_location: str, peer_data_locale: dict) -> str:
    if not last_seen_time:
        text = peer_data_locale['not_on_campus']
        return text[:text.index('.')]
    seconds = datetime.now(timezone('UTC')).timestamp() - last_seen_time
    seconds_in_day = int(timedelta(days=1).total_seconds())
    seconds_in_hour = int(timedelta(hours=1).total_seconds())
    seconds_in_minute = 60
    days = int(seconds // seconds_in_day)
    hours = int((seconds - (days * seconds_in_day)) // seconds_in_hour)
    minutes = int((seconds - (days * seconds_in_day) - (hours * seconds_in_hour)) // seconds_in_minute)
    days_gone = ''
    hours_gone = ''
    minutes_gone = ''
    if days:
        days_gone = f'{days}{peer_data_locale["days"]} '
    if hours:
        hours_gone = f'{hours}{peer_data_locale["hours"]} '
    if minutes:
        minutes_gone = f'{minutes}{peer_data_locale["minutes"]} '
    if not any((days, hours, minutes)):
        return peer_data_locale['just_now'].format(last_location=last_location)
    return peer_data_locale['not_on_campus'].format(days_gone=days_gone, hours_gone=hours_gone,
                                                    minutes_gone=minutes_gone, last_location=last_location)


async def peer_locations_compile(nickname: str, peer_locations_locale: dict, page: int = 0,
                                 message_text: str = None) -> Dict[str, Any]:
    peer_locations_data = {}
    locations = []
    if not page:
        locations_data = await intra_requests.get_peer_locations(nickname)
        if isinstance(locations_data, dict) and locations_data.get('error'):
            if '404' not in locations_data['error']:
                return {'text': f'<b>{nickname}</b>: {locations_data["error"]}', 'count': -1}
            return {'text': peer_locations_locale['not_found'].format(nickname=nickname.replace("<", "&lt")),
                    'count': -1}
        peer_data = await intra_requests.get_peer(nickname)
        peer = await Peer.from_dict(peer_data)
        title = get_peer_title(peer.status, peer.link, peer.full_name, peer.nickname)
        if not locations_data:
            return {'text': title + peer_locations_locale['not_logged'], 'count': 0}
        for location in locations_data:
            locations.append(await Host.from_dict(location))
        count = len(locations_data)
        data = []
        for location in locations[10:]:
            data.append({'campus': location.campus_name, 'host': location.host,
                         'begin_at': location.begin_at, 'end_at': location.end_at})
        if data:
            await mongo.update('peers', {'nickname': peer.nickname}, 'set', {'locations': data}, upsert=True)
        locations = locations[:10]
        peer_locations_data.update({'count': count})
    else:
        title = get_peer_title(*get_data_from_message(message_text))
        data = await mongo.find('peers', {'nickname': nickname})
        count = len(data['locations'][(page - 1) * 5:])
        for location in paginate(data['locations'], page - 1, 10):
            locations.append(Host.from_db(location))
        peer_locations_data.update({'count': count})
    texts = []
    for location in locations:
        text = f'<b>{location.campus_name}</b> <code>{location.host}</code>\n' \
               f'{get_log_time(location.begin_at, location.end_at, peer_locations_locale["now"])}'
        texts.append(text)
    peer_locations_data.update({'text': title + f'\n'.join(texts)})
    return peer_locations_data


async def host_data_compile(host_name: str, host_data_locale: dict, peer_data_locale: dict,
                            avatar: bool, page: int = 0, campus_name: str = None) -> Dict[str, Any]:
    if not page:
        host_data = await intra_requests.get_host(host_name)
        if not host_data:
            return {'text': host_data_locale['not_found'].format(host=host_name), 'error': True}
        if isinstance(host_data, dict) and host_data.get('error'):
            return {'text': f'<b>{host_name}</b>: {host_data["error"]}', 'error': True}
        hosts = []
        for host in host_data:
            hosts.append(await Host.from_dict(host))
        data = []
        for host in hosts:
            data.append({'peer': host.peer, 'begin_at': host.begin_at, 'end_at': host.end_at})
        await mongo.update('campuses', {'name': hosts[0].campus_name},
                           'set', {f'hosts.{hosts[0].host}': data}, upsert=True)
        host = hosts[0]
        campus_name = host.campus_name
    else:
        campus_data = await mongo.find('campuses', {'name': campus_name})
        data = campus_data['hosts'][host_name]
        campus_name = campus_data["name"]
        if page > 2:
            texts = []
            title = f'🖥 <b>{campus_data["name"]}</b> <code>{host_name}</code>\n'
            for host in data[3:]:
                log_time = get_log_time(host['begin_at'], host['end_at'], host_data_locale['now'])
                text = f'<code>{host["peer"]}</code>\n' \
                       f'{log_time}'
                texts.append(text)
            return {'text': title + '\n'.join(texts), 'host': host_name, 'several': True}
        else:
            host = Host.from_db(data, page)
    peer_data = await peer_data_compile(host.peer, peer_data_locale, True, avatar)
    if peer_data.get('error'):
        peer = host.peer
        peer_text = peer_data['text']
    else:
        lines = peer_data['text'].splitlines()
        peer_text = '\n'.join(lines[1:-2])
        peer = lines[0].replace('🟢 ', '')
        if host.end_at:
            peer_text = '\n'.join(lines[1:])
            peer = lines[0]
    if not page and host.end_at:
        peer = f'{host_data_locale["last_user"]}\n{peer}'
    log_time = get_log_time(host.begin_at, host.end_at, host_data_locale['now'])
    text = f'🖥 <b>{campus_name}</b> <code>{host_name}</code>\n' \
           f'{peer}\n' \
           f'{log_time}\n' \
           f'{peer_text}'
    return {'text': text, 'peer': host.peer, 'host': host_name, 'campus': campus_name}


async def peer_feedbacks_compile(nickname: str, peer_feedbacks_locale: dict,
                                 page: int = 0, message_text: str = None) -> Dict[str, Any]:
    peer_feedbacks_data = {}
    feedbacks = []
    if not page:
        feedbacks_data = await intra_requests.get_peer_feedbacks(nickname)
        if isinstance(feedbacks_data, dict) and feedbacks_data.get('error'):
            if '404' not in feedbacks_data['error']:
                return {'text': f'<b>{nickname}</b>: {feedbacks_data["error"]}', 'count': -1}
            return {'text': peer_feedbacks_locale['not_found'].format(nickname=nickname.replace("<", "&lt")),
                    'count': -1}
        peer_data = await intra_requests.get_peer(nickname)
        peer = await Peer.from_dict(peer_data)
        title = get_peer_title(peer.status, peer.link, peer.full_name, peer.nickname)
        if not feedbacks_data:
            return {'text': title + peer_feedbacks_locale['not_eval'], 'count': 0}
        for feedback in feedbacks_data:
            feedback_data = await Feedback.from_dict(feedback)
            if feedback_data:
                feedbacks.append(feedback_data)
        count = len(feedbacks)
        data = []
        for feedback in feedbacks[5:]:
            if feedback:
                data.append(
                    {'corrector_comment': feedback.corrector_comment, 'mark': feedback.mark, 'team': feedback.team,
                     'project': feedback.project, 'peer_nickname': feedback.peer_nickname,
                     'peer_link': feedback.peer_link, 'peer_comment': feedback.peer_comment,
                     'rating': feedback.rating, 'final_mark': feedback.final_mark})
        if data:
            await mongo.update('peers', {'nickname': peer.nickname}, 'set', {'feedbacks': data}, upsert=True)
        feedbacks = feedbacks[:5]
        peer_feedbacks_data.update({'count': count})
    else:
        title = get_peer_title(*get_data_from_message(message_text))
        data = await mongo.find('peers', {'nickname': nickname})
        count = len(data['feedbacks'][(page - 1) * 5:])
        for feedback in paginate(data['feedbacks'], page - 1, 5):
            feedbacks.append(Feedback.from_db(feedback))
        peer_feedbacks_data.update({'count': count})
    texts = []
    for feedback in feedbacks:
        link = f'<a href="{feedback.peer_link}">{feedback.peer_nickname}</a>'
        final_mark = feedback.final_mark
        if final_mark is None:
            final_mark = peer_feedbacks_locale["not_closed"]
        text = f'<b>{feedback.team}</b> [{feedback.project}]\n' \
               f'<b>{nickname}:</b> <i>{feedback.corrector_comment}</i>\n' \
               f'<b>{peer_feedbacks_locale["mark"]}:</b> {feedback.mark}\n' \
               f'{link}: <i>{feedback.peer_comment}</i>\n' \
               f'<b>{peer_feedbacks_locale["rating"]}:</b> {feedback.rating}/5\n' \
               f'<b>{peer_feedbacks_locale["final_mark"]}:</b> ' \
               f'{final_mark}'
        texts.append(text)
    peer_feedbacks_data.update({'text': title + f'\n{"—" * 20}\n'.join(texts)})
    return peer_feedbacks_data


async def free_locations_compile(campus_id: int, free_locations_locale: dict, page: int = 0) -> Dict[str, Any]:
    campus_data = await mongo.find('campuses', {'id': campus_id})
    if not campus_data:
        locations_data = None
        campus = await intra_requests.get_campus(campus_id)
        if campus.get('error'):
            return {'error': campus['error'], 'count': -1, 'scan_time': 0}
        time_zone = campus['time_zone']
        campus_name = campus['name']
        campus_data = {'time_zone': time_zone, 'name': campus_name}
    else:
        locations_data = campus_data.get('locations')
        time_zone = campus_data['time_zone']
        campus_name = campus_data['name']
        campus_data = {}
    three_minutes_ago = (datetime.now(timezone('UTC')) - timedelta(minutes=3)).timestamp()
    if not locations_data or locations_data['last_scan'] < three_minutes_ago:
        scan_time = datetime.now(timezone(time_zone))
        page = 0
        hours = 12
        pages = 4
        if 9 > scan_time.hour >= 0 or scan_time.hour > 21:
            hours = 24
            pages = 7
        past = scan_time - timedelta(hours=hours)
        locations = await intra_requests.get_campus_locations(campus_id, past, scan_time, pages)
        inactive = locations['inactive']
        active = locations['active']
        error = locations.get('error')
        if not error:
            locations = {}
            for location in inactive:
                if location['host'] not in locations:
                    locations.update({location['host']: {'peer': location['user']['login'],
                                                         'end_at': location['end_at']}})
            for location in active:
                locations.pop(location['host'], '')
            locations = list(locations.items())[:400]
            locations.sort()
            active = len(active)
            campus_data.update({'locations': {'last_scan': scan_time.timestamp(), 'data': locations,
                                              'active': active, 'hours': hours}})
            await mongo.update('campuses', {'id': campus_id}, 'set', campus_data, upsert=True)
        else:
            return {'error': locations['error'], 'count': -1, 'scan_time': 0}
    else:
        locations = locations_data['data']
        active = locations_data['active']
        hours = locations_data['hours']
        scan_time = datetime.fromtimestamp(locations_data['last_scan'])
    title = free_locations_locale['title'].format(campus_name=campus_name,
                                                  now=get_str_time(scan_time.isoformat(), time_zone),
                                                  active=active)
    texts = []
    count = len(locations[40 * page:])
    for location in paginate(locations, page, 40):
        text = f'<code>{location[0]}</code>  |  ' \
               f'<code>{location[1]["peer"]}</code>  |  ' \
               f'{get_str_time(location[1]["end_at"], time_zone)}'
        texts.append(text)
    body = free_locations_locale['disclaimer'].format(hours=hours)
    if texts:
        body = free_locations_locale['body'].format(hours=hours)
    return {'text': title + body + '\n'.join(texts), 'count': count,
            'page': page, 'scan_time': int(scan_time.timestamp())}


async def project_peers_compile(project_id: int, campus_id: int, campus_name: str,
                                time_zone: str, projects_locale: dict) -> Dict[str, Any]:
    project_data = await intra_requests.get_project_peers(project_id, campus_id, time_zone)
    if project_data.get('error'):
        return {'error': project_data['error']}
    weeks = project_data['weeks']
    title = projects_locale['not_found'].format(campus_name=campus_name, weeks=weeks)
    if project_data['data']:
        project_data['data'].sort(key=lambda key: get_utc(key['marked_at']), reverse=True)
        project_name = project_data['data'][0]['project']['name']
        title = projects_locale['title'].format(campus_name=campus_name, project_name=project_name, weeks=weeks)
    texts = []
    for project in project_data['data']:
        nickname = project["user"]["login"]
        link = f'<a href="https://profile.intra.42.fr/users/{nickname}">{nickname}</a>'
        text = f'{link}  |  ' \
               f'{project["final_mark"]}  |  ' \
               f'{get_str_time(project["marked_at"], time_zone)}'
        texts.append(text)
    return {'text': title + '\n'.join(texts)}
