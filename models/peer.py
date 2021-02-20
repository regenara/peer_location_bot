from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import List

from misc import intra_requests
from misc import mongo
from models.user import User
from utils.helpers import get_utc


@dataclass
class Peer:
    full_name: str = ''
    nickname: str = ''
    intra_id: int = 0
    pool: str = ''
    coalition: str = ''
    cursus_data: List[dict] = field(default_factory=list)
    campus: str = ''
    campus_id: int = 0
    time_zone: str = ''
    location: str = ''
    last_location: str = ''
    avatar: str = ''
    link: str = ''
    status: str = ''
    last_seen_time: float = .0
    is_staff: bool = False
    locations: List[dict] = field(default_factory=list)
    feedbacks: List[dict] = field(default_factory=list)
    username: str = ''
    user_id: int = 0
    stalkers: List[int] = field(default_factory=list)

    @staticmethod
    async def from_dict(data: dict) -> 'Peer':
        full_name = data['displayname']
        nickname = data['login']
        intra_id = data['id']
        pool = ''
        if data.get('pool_month') and data.get('pool_year'):
            months = {'january': '01', 'february': '02', 'march': '03',
                      'april': '04', 'may': '05', 'june': '06',
                      'july': '07', 'august': '08', 'september': '09',
                      'october': '10', 'november': '11', 'december': '12'}
            pool = f'{months[data["pool_month"]]}.{data["pool_year"]}'
        cursus_data = data['cursus_users']
        campus_id = [campus['campus_id'] for campus in data['campus_users'] if campus['is_primary']][0]
        campus, time_zone = [(campus['name'], campus['time_zone'])
                             for campus in data['campus'] if campus['id'] == campus_id][0]
        location = data['location']
        last_location = ''
        is_staff = data['staff?']
        avatar = data['image_url']
        link = f'https://profile.intra.42.fr/users/{nickname}'
        status = '🟢 '
        last_seen_time = .0
        if not location:
            status = '🔴 '
            locations = await intra_requests.get_peer_locations(nickname)
            if locations:
                last_seen_time = get_utc(locations[0]['end_at'])
                last_location = locations[0]['host']
                if not last_seen_time:
                    location = locations[0].host
                    status = '🟢 '
        if is_staff:
            status = '😎 '
        for cursus in cursus_data:
            now = datetime.now().timestamp()
            if cursus['cursus']['name'] == '42cursus':
                end_at = get_utc(cursus['end_at'])
                if end_at and end_at < now and cursus['level'] < 16:
                    status = '☠️ '
                break
        coalition = ''
        peer_coalitions = await intra_requests.get_peer_coalitions(nickname)
        if peer_coalitions:
            coalition_id = peer_coalitions[0]['coalition_id']
            coalition_data = await mongo.find('coalitions', {'coalition_id': coalition_id})
            if coalition_data is None:
                coalition_data = await intra_requests.get_coalition(coalition_id)
                if not coalition_data.get('error'):
                    coalition_data = await mongo.update(
                        'coalitions', {'coalition_id': coalition_id}, 'set',
                        {'name': coalition_data['name']}, upsert=True, return_document=True
                    )
            coalition = coalition_data.get('name') or ''
        peer_in_db = await mongo.find('users', {'nickname': nickname})
        username = ''
        if peer_in_db:
            user = User.from_dict(peer_in_db)
            if not user.anon and user.username:
                username = user.username
        return Peer(full_name, nickname, intra_id, pool, coalition, cursus_data, campus, campus_id, time_zone, location,
                    last_location, avatar, link, status, last_seen_time, is_staff, username=username)

    @staticmethod
    def short_data(data: dict) -> 'Peer':
        nickname = data['login']
        intra_id = data['id']
        campus_id = [campus['campus_id'] for campus in data['campus_users'] if campus['is_primary']][0]
        campus, time_zone = [(campus['name'], campus['time_zone'])
                             for campus in data['campus'] if campus['id'] == campus_id][0]
        location = data['location']
        return Peer(nickname=nickname, intra_id=intra_id, campus=campus,
                    campus_id=campus_id, time_zone=time_zone, location=location)

    @staticmethod
    def from_db(data: dict) -> 'Peer':
        nickname = data['nickname']
        username = data.get('username')
        user_id = data.get('user_id')
        intra_id = data.get('intra_id')
        campus_id = data.get('campus_id')
        campus = data.get('campus')
        locations = data.get('locations', 'not_in_db')
        time_zone = data.get('time_zone')
        feedbacks = data.get('feedbacks')
        location = data.get('location')
        stalkers = data.get('stalkers')
        return Peer(nickname=nickname, intra_id=intra_id, username=username, user_id=user_id,
                    locations=locations, feedbacks=feedbacks, location=location, stalkers=stalkers,
                    campus=campus, campus_id=campus_id, time_zone=time_zone)
