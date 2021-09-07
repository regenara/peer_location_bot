from typing import (Any,
                    Dict)

from utils.cache import (cache,
                         del_cache)
from . import db


class Coalition(db.Model):
    __tablename__ = 'coalitions'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.to_dict()})'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Coalition':
        coalition = cls()
        for k, v in data.items():
            setattr(coalition, k, v)
        return coalition

    @classmethod
    @cache(serialization=True, deserialization=True)
    async def get_coalition(cls, coalition_id: int) -> 'Coalition':
        return await cls.get(coalition_id)

    @classmethod
    @del_cache(keys=['Coalition.get_coalition'])
    async def create_coalition(cls, coalition_id: int, name: str) -> 'Coalition':
        return await cls.create(id=coalition_id, name=name)
