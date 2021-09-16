from config import Config
from db_models.campuses import Campus
from db_models.coalitions import Coalition
from db_models.peers import Peer
from db_models.projects import Project
from utils.cache import Cache
from utils.intra_api import (UnknownIntraError,
                             NotFoundIntraError)


class Savers:
    @staticmethod
    async def get_peer(peer_id: int, login: str, campus_id: int, user_id: int = None) -> Peer:
        peer = await Peer.get_peer(peer_id=peer_id)
        updates = {}
        if peer and user_id:
            updates.update({'user_id': user_id})
        if peer and peer.campus_id != campus_id:
            updates.update({'campus_id': campus_id})
        if updates:
            peer = await Peer.update_peer(peer_id=peer_id, **updates)
            keys = [f'User.get_user_from_peer:{peer_id}', f'User.get_user_data:{user_id}']
            [await Cache().delete(key=key) for key in keys]
        if not peer:
            peer = await Peer.create_peer(peer_id=peer_id, login=login, campus_id=campus_id, user_id=user_id)
        return peer

    @staticmethod
    async def get_campus(campus_id: int) -> Campus:
        campus = await Campus.get_campus(campus_id=campus_id)
        if not campus:
            campus_data = await Config.intra.get_campus(campus_id=campus_id)
            campus = await Campus.create_campus(campus_id=campus_id, name=campus_data['name'],
                                                time_zone=campus_data['time_zone'])
        return campus

    @staticmethod
    async def get_coalition(coalition_id: int) -> Coalition:
        coalition = await Coalition.get_coalition(coalition_id=coalition_id)
        if not coalition:
            coalition_data = await Config.intra.get_coalition(coalition_id=coalition_id)
            coalition = await Coalition.create_coalition(coalition_id=coalition_data['id'],
                                                         name=coalition_data['name'])
        return coalition

    @staticmethod
    async def get_project(project_id: int, project_gitlab_path: str = None) -> Project:
        project = await Project.get_project(project_id=project_id)
        if not project:
            try:
                project_data = await Config.intra.get_project(project_id=project_id)
            except (UnknownIntraError, NotFoundIntraError):
                return Project(id=project_id, name=f'Project id{project_id}')
            name = f'Project id{project_id}' if not project_gitlab_path else project_gitlab_path.split('/')[-1]
            if project_data:
                name = project_data['name']
            cursus_id = project_data['cursus'][0]['id'] if project_data else None
            project = await Project.create_project(project_id=project_id, name=name, cursus_id=cursus_id)
        return project
