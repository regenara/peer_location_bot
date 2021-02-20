from dataclasses import dataclass
from dataclasses import field
from typing import List


@dataclass
class User:
    user_id: int = 0
    username: str = ''
    nickname: str = ''
    campus: str = ''
    campus_id: int = 0
    time_zone: str = ''
    avatar: bool = False
    lang: str = ''
    anon: bool = True
    friends: List[str] = field(default_factory=list)
    notifications: List[str] = field(default_factory=list)
    friends_count: int = 0
    notifications_count: int = 0

    @staticmethod
    def from_dict(data: dict) -> 'User':
        user_id = data['user_id']
        username = data.get('username')
        nickname = data.get('nickname')
        campus = data.get('campus')
        campus_id = data.get('campus_id')
        time_zone = data.get('time_zone')
        avatar = data.get('settings', {}).get('avatar') or False
        lang = data.get('settings', {}).get('lang') or 'en'
        anon = data.get('settings', {}).get('anon')
        if anon is None:
            anon = True
        friends = data.get('friends', [])
        notifications = data.get('notifications', [])
        friends_count = len(friends)
        notifications_count = len(notifications)
        return User(user_id, username, nickname, campus, campus_id, time_zone, avatar, lang, anon,
                    friends, notifications, friends_count, notifications_count)
