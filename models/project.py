from dataclasses import (dataclass,
                         field)
from typing import (Any,
                    Dict,
                    List)

from .peer import Cursus


@dataclass
class Project:
    final_mark: int = 0
    status: str = ''
    validated: bool = False
    id: int = 0
    name: str = ''
    parent_id: int = 0
    cursus_ids: List[int] = field(default_factory=list)
    children: List['Project'] = field(default_factory=list)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Project':
        final_mark = data['final_mark']
        status = data['status']
        validated = data['validated?']
        id = data['project']['id']
        name = data['project']['name']
        parent_id = data['project']['parent_id']
        cursus_ids = data['cursus_ids']
        children = []
        return Project(final_mark=final_mark, status=status, validated=validated, id=id,
                       parent_id=parent_id, name=name, cursus_ids=cursus_ids, children=children)

    @staticmethod
    def _compile_projects(projects_data: List['Project'], courses: Dict[int, Any]) -> Dict[str, List['Project']]:
        children = {}
        for project in projects_data:
            if project.parent_id:
                children.setdefault(project.parent_id, []).append(project)
        projects = {}
        statuses = {
            'finished': '❌',
            'in_progress': '📝',
            'waiting_for_correction': '⏳',
            'searching_a_group': '🕵️‍♂️',
            'creating_group': '👥',
            'waiting_to_start': '⏯',
            'parent': '👩‍👦'
        }
        for project in projects_data:
            if not project.cursus_ids:
                continue
            cursus = project.cursus_ids[0]
            for cursus_id in project.cursus_ids:
                cursus = courses.get(cursus_id)
                if cursus:
                    break
            project.status = statuses.get(project.status) or '❓'
            if project.validated:
                project.status = '✅'
            project.children.extend(children.get(project.id, []))
            if not project.parent_id:
                projects.setdefault(cursus, []).append(project)
        return projects

    def from_list(self, projects_data: List[Dict[str, Any]], cursus_data: List[Cursus]) -> Dict[str, List['Project']]:
        courses = {cursus.cursus_id: cursus.name for cursus in cursus_data}
        projects_data = [self.from_dict(data=project) for project in projects_data]
        return self._compile_projects(projects_data=projects_data, courses=courses)
