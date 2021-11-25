from dataclasses import (dataclass,
                         field)
from datetime import (datetime,
                      timezone)
from typing import (Any,
                    Dict,
                    List,
                    Tuple,
                    Optional)

from config import Config
from db_models.users import User
from models.host import Host
from utils.savers import Savers


@dataclass
class Cursus:
    id: int = 0
    cursus_id: int = 0
    name: str = ''
    level: float = 0.0
    end_at: Optional[datetime] = None

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Cursus':
        id = data['id']
        cursus_id = data['cursus']['id']
        name = data['cursus']['name']
        level = round(data['level'], 2)
        end_at = datetime.fromisoformat(data['end_at'].replace('Z', '+00:00')) if data['end_at'] else None
        return Cursus(id=id, cursus_id=cursus_id, name=name, level=level, end_at=end_at)


@dataclass
class Peer:
    id: int = 0
    login: str = ''
    full_name: str = ''
    pool_month: str = ''
    pool_year: str = ''
    coalition: str = ''
    cursus_data: List[Cursus] = field(default_factory=list)
    cursus: Optional[Cursus] = None
    campus: str = ''
    campus_id: int = 0
    time_zone: str = ''
    location: str = ''
    last_location: str = ''
    avatar: str = ''
    link: str = ''
    status: str = ''
    last_seen_time: str = ''
    is_staff: bool = False
    dignity: str = ''
    username: str = ''
    projects_users: List[Dict[str, Any]] = field(default_factory=list)

    @staticmethod
    async def _get_coalition(login: str) -> str:
        coalitions = await Config.intra.get_peer_coalitions(login=login)
        if coalitions:
            coalition_id = coalitions[0]['coalition_id']
            coalition = await Savers.get_coalition(coalition_id=coalition_id)
            return coalition.name

    @staticmethod
    async def _get_username(peer_id: int) -> str:
        user = await User.get_user_from_peer(peer_id=peer_id)
        if user and user.username and user.show_me:
            return user.username

    async def _get_extended_data(self, login: str, peer_id: int, location: str,
                                 status: str) -> Tuple[str, str, str, str, str, str]:
        last_location = ''
        last_seen_time = ''
        if not location:
            locations = await Host().get_peer_locations(login=login)
            if locations:
                last_seen_time = locations[0].end_at
                last_location = locations[0].host
                if not last_seen_time:
                    location = locations[0].host
                    status = '🟢 '
        coalition = await self._get_coalition(login=login) or ''
        username = await self._get_username(peer_id=peer_id) or ''
        return status, location, last_location, last_seen_time, coalition, username

    async def get_peer(self, login: str, extended: bool = True) -> 'Peer':
        peer_data = await Config.intra.get_peer(login=login)
        if peer_data:
            id = peer_data['id']
            full_name = peer_data['displayname']
            login = peer_data['login']
            pool_month = peer_data.get('pool_month')
            pool_year = peer_data.get('pool_year')
            cursus_data = sorted([Cursus.from_dict(data=cursus) for cursus in peer_data['cursus_users']],
                                 key=lambda cursus: cursus.id)
            cursus = cursus_data[-1] if cursus_data else None
            campus_id = [campus['campus_id'] for campus in peer_data['campus_users'] if campus['is_primary']][0]
            campus, time_zone = [(campus['name'], campus['time_zone'])
                                 for campus in peer_data['campus'] if campus['id'] == campus_id][0]
            location = peer_data['location']
            is_staff = peer_data['staff?']
            avatar = peer_data['image_url']
            link = f'https://profile.intra.42.fr/users/{login}'
            status = '🟢 '
            if not location:
                status = '🔴 '
            if cursus and (cursus.id == Config.cursus_id) and cursus.end_at and \
                    (cursus.end_at < datetime.now(timezone.utc)) and (cursus.level < 16):
                status = '☠️ '
            if login == 'mstoneho':
                status = '🗿 '
            dignity = ''
            if peer_data['titles']:
                selected = [title_user['title_id'] for title_user in peer_data['titles_users']
                            if title_user['selected']]
                if selected:
                    dignity = [title['name'] for title in peer_data['titles'] if title['id'] == selected[0]][0]
            coalition = username = last_seen_time = last_location = ''
            if extended:
                status, location, last_location, last_seen_time, coalition, username = \
                    await self._get_extended_data(login=login, peer_id=id, location=location, status=status)
            if is_staff:
                status = '😎 '
            projects_users = sorted(peer_data['projects_users'], key=lambda project: project['id'], reverse=True)
            await Savers.get_peer(peer_id=id, login=login, cursus_id=cursus.cursus_id, campus_id=campus_id)
            return Peer(id=id, login=login, full_name=full_name, pool_month=pool_month, pool_year=pool_year,
                        coalition=coalition, cursus_data=cursus_data, cursus=cursus, campus=campus,
                        campus_id=campus_id, time_zone=time_zone, location=location, last_location=last_location,
                        avatar=avatar, link=link, status=status, last_seen_time=last_seen_time, is_staff=is_staff,
                        dignity=dignity, username=username, projects_users=projects_users)
