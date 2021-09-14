from typing import (Any,
                    Dict,
                    List)

from utils.cache import cache
from . import db


class Application(db.Model):
    __tablename__ = 'applications'

    id = db.Column(db.Integer(), primary_key=True)
    client_id = db.Column(db.String(128), nullable=False, unique=True)
    client_secret = db.Column(db.String(128), nullable=False, unique=True)
    is_main = db.Column(db.Boolean(), nullable=True, unique=True)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.to_dict()})'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'is_main': self.is_main
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Application':
        application = cls()
        for k, v in data.items():
            setattr(application, k, v)
        return application

    @classmethod
    @cache(serialization=True, deserialization=True)
    async def get_all(cls) -> List['Application']:
        return await cls.query.where((cls.is_main.is_(True) | cls.is_main.is_(None))).gino.all()

    @classmethod
    async def get_main(cls) -> 'Application':
        return await cls.query.where(cls.is_main.is_(True)).gino.first()

    @classmethod
    async def get_test(cls) -> 'Application':
        return await cls.query.where(cls.is_main.is_(False)).gino.first()
