from enum import Enum
from typing import (Any,
                    Dict,
                    List)

from utils.cache import (cache,
                         del_cache)
from . import db
from .peers import Peer


class Relationship(Enum):
    friend = 'friend'
    observable = 'observable'


class UserPeer(db.Model):
    __tablename__ = 'users_peers'

    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    peer_id = db.Column(db.ForeignKey('peers.id', ondelete='CASCADE'), nullable=False)
    relationship = db.Column(db.Enum(Relationship), nullable=False)

    _uniq = db.UniqueConstraint('user_id', 'peer_id', 'relationship')

    @classmethod
    @cache()
    async def _get_relationships(cls, user_id: int) -> Dict[str, List[Dict[str, Any]]]:
        query = db.select([Peer, cls]).select_from(Peer.join(cls)).where(cls.user_id == user_id).order_by(cls.id)
        result = await query.gino.load((Peer, cls)).all()
        relationships = {'friends': [], 'observables': []}
        for peer, peer_users in result:
            if peer_users.relationship is Relationship.friend:
                relationships['friends'].append(peer.to_dict())
            else:
                relationships['observables'].append(peer.to_dict())
        return relationships

    @classmethod
    async def get_friends_count(cls, user_id: int) -> int:
        return len(await cls.get_friends(user_id=user_id))

    @classmethod
    @del_cache(keys=['UserPeer._get_relationships'])
    async def add_friend(cls, user_id: int, peer_id: int):
        await cls.create(user_id=user_id, peer_id=peer_id, relationship=Relationship.friend)

    @classmethod
    @del_cache(keys=['UserPeer._get_relationships'])
    async def remove_friend(cls, user_id: int, peer_id: int):
        await cls.delete.where(
            (cls.user_id == user_id) & (cls.peer_id == peer_id) & (cls.relationship == Relationship.friend)
        ).gino.status()

    @classmethod
    async def get_friends(cls, user_id: int) -> List[Peer]:
        relationships = await cls._get_relationships(user_id=user_id)
        return [Peer.from_dict(friend) for friend in relationships['friends']]

    @classmethod
    async def get_observed_count(cls, user_id: int) -> int:
        return len(await cls.get_observables(user_id=user_id))

    @classmethod
    @del_cache(keys=['UserPeer._get_relationships'])
    async def add_observable(cls, user_id: int, peer_id: int):
        await cls.create(user_id=user_id, peer_id=peer_id, relationship=Relationship.observable)

    @classmethod
    @del_cache(keys=['UserPeer._get_relationships'])
    async def remove_observable(cls, user_id: int, peer_id: int):
        await cls.delete.where(
            (cls.user_id == user_id) & (cls.peer_id == peer_id) & (cls.relationship == Relationship.observable)
        ).gino.status()

    @classmethod
    async def get_observables(cls, user_id: int) -> List[Peer]:
        relationships = await cls._get_relationships(user_id=user_id)
        return [Peer.from_dict(observable) for observable in relationships['observables']]
