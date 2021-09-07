from typing import List

from utils.cache import (cache,
                         del_cache)
from . import db


class Campus(db.Model):
    __tablename__ = 'campuses'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    time_zone = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.to_dict()})'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'time_zone': self.time_zone
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Campus':
        campus = cls()
        for k, v in data.items():
            setattr(campus, k, v)
        return campus

    @classmethod
    @cache(serialization=True, deserialization=True)
    async def get_campus(cls, campus_id: int) -> 'Campus':
        return await cls.get(campus_id)

    @classmethod
    @cache(serialization=True, deserialization=True)
    async def get_campuses(cls) -> List['Campus']:
        return await cls.query.order_by(cls.name).gino.all()

    @classmethod
    @del_cache(keys=['Campus.get_campus', 'Campus.get_campuses'], without_sub_key=[1])
    async def create_campus(cls, campus_id: int, name: str, time_zone: str) -> 'Campus':
        return await cls.create(id=campus_id, name=name, time_zone=time_zone)
