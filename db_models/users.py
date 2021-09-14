from enum import Enum
from typing import (Any,
                    Dict,
                    Tuple)

from sqlalchemy.sql import expression

from utils.cache import (Cache,
                         cache,
                         del_cache)
from . import db
from .campuses import Campus
from .mixins.time import TimeMixin
from .peers import Peer


class Languages(Enum):
    ru = 'ru'
    en = 'en'


class User(db.Model, TimeMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(50), nullable=True)
    show_avatar = db.Column(db.Boolean(), nullable=False, server_default=expression.false())
    show_me = db.Column(db.Boolean(), nullable=False, server_default=expression.false())
    use_default_campus = db.Column(db.Boolean(), nullable=False, server_default=expression.true())
    language = db.Column(db.Enum(Languages), nullable=False, server_default=Languages.en.name)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.to_dict()})'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'show_avatar': self.show_avatar,
            'show_me': self.show_me,
            'use_default_campus': self.use_default_campus,
            'language': self.language.value if hasattr(self.language, 'value') else self.language
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        user = cls()
        for k, v in data.items():
            setattr(user, k, v)
        return user

    @classmethod
    @cache(serialization=True, deserialization=True)
    async def get_user_from_peer(cls, peer_id: int) -> 'User':
        return await cls.query.select_from(Peer.join(User)).where(Peer.id == peer_id).gino.first()

    @classmethod
    @cache()
    async def get_login_from_username(cls, username: str) -> str:
        return await Peer.query.select_from(Peer.join(cls)).where(
            (db.func.lower(cls.username) == username) & (cls.show_me.is_(True))).gino.load(Peer.login).first()

    @classmethod
    @cache(serialization=True)
    async def get_user_data(cls, user_id: int) -> Tuple[Campus, Peer, 'User']:
        query = db.select([Campus, Peer, cls]).select_from(Campus.join(Peer).join(cls)).where(Peer.user_id == user_id)
        return await query.gino.load((Campus, Peer, cls)).first()

    @classmethod
    @del_cache(keys=['User.get_user_data'])
    async def create_user(cls, user_id: int, username: str, language: str, show_avatar: bool,
                          show_me: bool, use_default_campus: bool) -> 'User':
        return await cls.create(id=user_id, username=username, language=language, show_avatar=show_avatar,
                                show_me=show_me, use_default_campus=use_default_campus)

    @classmethod
    async def update_user(cls, user_id: int, **kwargs) -> 'User':
        _, peer, user = await cls.get_user_data(user_id=user_id)
        if isinstance(user, dict):
            user = cls.from_dict(data=user)
            peer = Peer.from_dict(data=peer)
        keys = [f'User.get_user_data:{user_id}', f'User.get_user_from_peer:{peer.id}']
        if user.username:
            keys.append(f'User.get_login_from_username:{user.username.lower()}')
        await user.update(**kwargs).apply()
        [await Cache().delete(key=key) for key in keys]
        return user
