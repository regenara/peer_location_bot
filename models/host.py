from dataclasses import dataclass

from misc import intra_requests
from misc import mongo
from utils.helpers import get_str_time
from utils.helpers import get_utc


@dataclass
class Host:
    campus_name: str = ''
    host: str = ''
    peer: str = ''
    begin_at: str = ''
    end_at: str = ''
    end_at_utc: float = .0

    @staticmethod
    async def from_dict(data: dict) -> 'Host':
        host = data['host']
        peer = data['user']['login']
        campus_id = data['campus_id']
        campus_data = await mongo.find('campuses', {'id': campus_id})
        if campus_data is None:
            campus_data = await intra_requests.get_campus(campus_id)
            if not campus_data.get('error'):
                campus_data = await mongo.update(
                    'campuses', {'id': campus_id}, 'set',
                    {'name': campus_data['name'], 'time_zone': campus_data['time_zone']},
                    upsert=True, return_document=True
                )
        campus_name = campus_data.get('name') or campus_id
        time_zone = campus_data.get('time_zone') or 'UTC'
        begin_at = get_str_time(data['begin_at'], time_zone)
        end_at = get_str_time(data['end_at'], time_zone)
        end_at_utc = get_utc(data['end_at'])
        return Host(campus_name, host, peer, begin_at, end_at, end_at_utc)

    @staticmethod
    def from_db(data: dict, page: int = None) -> 'Host':
        if page is not None:
            peer = data[page]['peer']
            begin_at = data[page]['begin_at']
            end_at = data[page]['end_at']
            return Host(peer=peer, begin_at=begin_at, end_at=end_at)
        else:
            campus = data['campus']
            host = data['host']
            peer = data.get('user', {}).get('login', {}) or ''
            begin_at = data['begin_at']
            end_at = data['end_at']
            return Host(peer=peer, begin_at=begin_at, end_at=end_at, campus_name=campus, host=host)
