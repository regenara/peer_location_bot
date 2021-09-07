from utils.cache import (cache,
                         del_cache)
from . import db
from .mixins.time import TimeMixin


class Peer(db.Model, TimeMixin):
    __tablename__ = 'peers'

    id = db.Column(db.Integer(), primary_key=True)
    login = db.Column(db.String(50), nullable=False, unique=True)
    campus_id = db.Column(db.ForeignKey('campuses.id', ondelete='SET NULL'), nullable=True)
    user_id = db.Column(db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.to_dict()})'

    def to_dict(self):
        return {
            'id': self.id,
            'login': self.login,
            'campus_id': self.campus_id,
            'user_id': self.user_id
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Peer':
        peer = cls()
        for k, v in data.items():
            setattr(peer, k, v)
        return peer

    @classmethod
    @cache(serialization=True, deserialization=True)
    async def get_peer(cls, peer_id: int) -> 'Peer':
        return await cls.get(peer_id)

    @classmethod
    @del_cache(keys=['Peer.get_peer'])
    async def create_peer(cls, peer_id: int, login: str, campus_id: int = None, user_id: int = None) -> 'Peer':
        return await cls.create(id=peer_id, login=login, campus_id=campus_id, user_id=user_id)

    @classmethod
    @del_cache(keys=['Peer.get_peer'])
    async def update_peer(cls, peer_id: int, **kwargs) -> 'Peer':
        peer = await cls.get(peer_id)
        await peer.update(**kwargs).apply()
        return peer



