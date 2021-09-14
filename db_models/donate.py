from datetime import (datetime,
                      timedelta)
from decimal import Decimal
from typing import (List,
                    Tuple)

from gino.loader import ColumnLoader

from utils.cache import cache
from . import db
from .mixins.time import TimeMixin


class Donate(db.Model, TimeMixin):
    __tablename__ = 'donate'

    uid = db.Column(db.String(128), nullable=False, unique=True)
    nickname = db.Column(db.String(40), nullable=True)
    sum = db.Column(db.Numeric(10, 2), nullable=False)
    message = db.Column(db.Text(), nullable=True)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.to_dict()})'

    def to_dict(self):
        return {
            'uid': self.uid,
            'nickname': self.nickname,
            'sum': self.sum,
            'message': self.message
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Donate':
        donate = cls()
        for k, v in data.items():
            setattr(donate, k, v)
        return donate

    @classmethod
    @cache(serialization=True, deserialization=True)
    async def get_last_month_donate(cls) -> List['Donate']:
        past = datetime.utcnow() - timedelta(days=datetime.now().day)
        return await cls.query.where(cls.created_at > past).order_by(cls.created_at.desc()).gino.all()

    @classmethod
    @cache()
    async def get_top_donaters(cls) -> Tuple[str, Decimal]:
        sums = db.func.sum(cls.sum)
        return await db.select([cls.nickname, sums]).group_by(
            cls.nickname).order_by(sums.desc()).limit(20).gino.load((cls.nickname, ColumnLoader(sums))).all()
