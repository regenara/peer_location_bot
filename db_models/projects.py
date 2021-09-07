from contextlib import suppress
from typing import (Any,
                    Dict,
                    List)

import asyncpg.exceptions

from utils.cache import (Cache,
                         cache,
                         del_cache)
from . import db


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    cursus_id = db.Column(db.Integer(), nullable=True)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.to_dict()})'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'cursus_id': self.cursus_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        project = cls()
        for k, v in data.items():
            setattr(project, k, v)
        return project

    @classmethod
    @cache(serialization=True, deserialization=True)
    async def get_project(cls, project_id: int) -> 'Project':
        return await cls.get(project_id)

    @classmethod
    @cache(serialization=True, deserialization=True)
    async def get_projects(cls, cursus_id: int) -> List['Project']:
        return await cls.query.where(cls.cursus_id == cursus_id).order_by(cls.name).gino.all()

    @classmethod
    @del_cache(keys=['Project.get_project'])
    async def create_project(cls, project_id: int, name: str, cursus_id: int) -> 'Project':
        await Cache().delete(key=f'Project.get_projects:{cursus_id}')
        with suppress(asyncpg.exceptions.UniqueViolationError):
            return await cls.create(id=project_id, name=name, cursus_id=cursus_id)

    @classmethod
    @del_cache(keys=['Project.get_projects'])
    async def delete_projects_from_cursus(cls, cursus_id: int, project_ids: List[int]):
        async with db.transaction():
            await cls.update.values(cursus_id=None).where(
                (cls.cursus_id == cursus_id) & (cls.id.notin_(project_ids))).gino.status()
        for project_id in project_ids:
            await Cache().delete(key=f'Project.get_project:{project_id}')
