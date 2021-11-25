from dataclasses import dataclass
from typing import (Any,
                    Dict,
                    List,
                    Optional)


@dataclass
class Event:
    id: int = 0
    name: str = ''
    description: str = ''
    location: str = ''
    begin_at: str = ''
    end_at: str = ''
    kind: str = ''
    nbr_subscribers: int = 0
    max_people: Optional[int] = None

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Event':
        id = data['id']
        name = data['name'].replace("<", "&lt")
        description = data.get('description', '').replace("<", "&lt")
        location = (data['location'] or '').replace("<", "&lt")
        begin_at = data['begin_at']
        end_at = data['end_at']
        kind = data.get('kind', 'exam')
        nbr_subscribers = data['nbr_subscribers']
        max_people = data['max_people']
        return Event(id=id, name=name, description=description, location=location, begin_at=begin_at, end_at=end_at,
                     kind=kind, nbr_subscribers=nbr_subscribers, max_people=max_people)

    def from_list(self, events_data: List[Dict[str, Any]]) -> List['Event']:
        return [self.from_dict(data=event) for event in events_data]
