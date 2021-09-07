from dataclasses import dataclass
from typing import (Any,
                    Dict,
                    List)

from config import Config


@dataclass
class Host:
    end_at: str = ''
    begin_at: str = ''
    host: str = ''
    campus_id: int = 0
    login: str = ''
    peer_id: int = 0

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Host':
        end_at = data['end_at']
        begin_at = data['begin_at']
        host = data['host']
        campus_id = data['campus_id']
        login = data['user']['login']
        peer_id = data['user']['id']
        return Host(end_at=end_at, begin_at=begin_at, host=host, campus_id=campus_id, login=login, peer_id=peer_id)

    async def get_peer_locations(self, login: str) -> List['Host']:
        peer_locations = await Config.intra.get_peer_locations(login=login)
        return self._from_list(location_records=peer_locations)

    async def get_location_history(self, host: str) -> List['Host']:
        location_records = await Config.intra.get_location_history(host=host)
        return self._from_list(location_records=location_records)

    def _from_list(self, location_records: List[Dict[str, Any]]) -> List['Host']:
        records = []
        for data in location_records:
            location = self.from_dict(data=data)
            records.append(location)
        return records
