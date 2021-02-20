from dataclasses import dataclass
from typing import Any
from typing import Union

from misc import intra_requests
from misc import mongo


@dataclass
class Feedback:
    corrector_comment: str = ''
    mark: int = 0
    team: str = ''
    project: str = ''
    peer_nickname: str = ''
    peer_link: str = ''
    peer_comment: str = ''
    rating: int = 0
    final_mark: Any = None

    @staticmethod
    async def from_dict(data: dict) -> Union['Feedback', None]:
        corrector_comment = (data['comment'] or '').replace("<", "&lt")
        peer_comment = (data['feedback'] or '').replace("<", "&lt")
        if corrector_comment and peer_comment:
            mark = data['final_mark']
            team = data['team']['name']
            peer_nickname = 'SYSTEM'
            peer_link = 'https://profile.intra.42.fr/'
            if data['feedbacks'][0]['user'] is not None:
                peer_nickname = data['feedbacks'][0]['user']['login']
                peer_link = f'https://profile.intra.42.fr/users/{peer_nickname}'
            rating = data['feedbacks'][0]['rating']
            final_mark = data['team']['final_mark']
            project_id = data['team']['project_id']
            project_data = await mongo.find('projects', {'project_id': project_id})
            if project_data is None:
                project_data = await intra_requests.get_project(project_id)
                if not project_data.get('error'):
                    project_data = await mongo.update(
                        'projects', {'project_id': project_id}, 'set',
                        {'name': project_data['name'], 'slug': project_data['slug']},
                        upsert=True, return_document=True
                    )
            project = project_data.get('name') or project_id
            return Feedback(corrector_comment, mark, team, project, peer_nickname,
                            peer_link, peer_comment, rating, final_mark)

    @staticmethod
    def from_db(data: dict) -> 'Feedback':
        corrector_comment = data['corrector_comment']
        mark = data['mark']
        team = data['team']
        project = data['project']
        peer_nickname = data['peer_nickname']
        peer_link = data['peer_link']
        peer_comment = data['peer_comment']
        rating = data['rating']
        final_mark = data['final_mark']
        return Feedback(corrector_comment, mark, team, project, peer_nickname,
                        peer_link, peer_comment, rating, final_mark)
