from dataclasses import dataclass
from typing import (Any,
                    Dict,
                    List)

from aiogram.utils.markdown import hlink

from config import Config
from utils.savers import Savers


@dataclass
class Feedback:
    corrector_comment: str = ''
    mark: int = 0
    team: str = ''
    project: str = ''
    peer: str = ''
    peer_comment: str = ''
    rating: int = 0
    final_mark: Any = None

    @staticmethod
    async def from_dict(data: Dict[str, Any]) -> 'Feedback':
        corrector_comment = (data['comment'] or '').replace("<", "&lt")
        peer_comment = (data['feedback'] or '').replace("<", "&lt")
        if corrector_comment and peer_comment:
            mark = data['final_mark']
            team = data['team']['name']
            peer = 'SYSTEM'
            if data['feedbacks'][0]['user'] is not None:
                peer_login = data['feedbacks'][0]['user']['login']
                peer_link = f'https://profile.intra.42.fr/users/{peer_login}'
                peer = hlink(title=peer_login, url=peer_link)
            rating = data['feedbacks'][0]['rating']
            final_mark = data['team']['final_mark']
            project_id = data['team']['project_id']
            project = await Savers.get_project(project_id=project_id,
                                               project_gitlab_path=data['team']['project_gitlab_path'])
            return Feedback(corrector_comment=corrector_comment, mark=mark, team=team, project=project.name,
                            peer=peer, peer_comment=peer_comment, rating=rating, final_mark=final_mark)

    async def get_peer_feedbacks(self, login: str) -> List['Feedback']:
        feedbacks = []
        feedbacks_data = await Config.intra.get_peer_feedbacks(login=login)
        for data in feedbacks_data:
            feedback = await self.from_dict(data=data)
            if feedback:
                feedbacks.append(feedback)
        return feedbacks
