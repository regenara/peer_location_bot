from typing import Union

from aiogram.dispatcher.filters.filters import BoundFilter
from aiogram.dispatcher.handler import ctx_data
from aiogram.types import (CallbackQuery,
                           Message)

from config import Config
from db_models.users_peers import UserPeer


class IsUnauthorized(BoundFilter):
    key = 'is_unauthorized'

    def __init__(self, is_unauthorized):
        self.is_unauthorized = is_unauthorized

    async def check(self, message: Union[Message, CallbackQuery]) -> bool:
        data = ctx_data.get()
        return not data['user_data']


class IsMailing(BoundFilter):
    key = 'is_mailing'

    def __init__(self, is_mailing):
        self.is_mailing = is_mailing

    async def check(self, message: Message) -> bool:
        return message.text == '$' and message.from_user.id == Config.admin


class IsUpdateProjects(BoundFilter):
    key = 'is_update_projects'

    def __init__(self, is_update_projects):
        self.is_update_projects = is_update_projects

    async def check(self, message: Message) -> bool:
        return message.text == '€' and message.from_user.id == Config.admin


class IsIntrovert(BoundFilter):
    key = 'is_introvert'

    def __init__(self, is_introvert):
        self.is_introvert = is_introvert

    async def check(self, message: Message) -> bool:
        friends_count = await UserPeer.get_friends_count(user_id=message.from_user.id)
        return message.text in ('/friends', Config.local.friends.ru, Config.local.friends.en) and friends_count < 2


class IsRemoveFriend(BoundFilter):
    key = 'is_remove_friend'

    def __init__(self, is_remove_friend):
        self.is_remove_friend = is_remove_friend

    async def check(self, callback_query: CallbackQuery) -> bool:
        message_text = callback_query.message.text or ''
        remove = callback_query.data.split('.')[0] == 'remove'
        title = message_text.split('\n')[0]
        try:
            return any(title[:title.rindex(' ')] in s for s in
                       (Config.local.friends_list.ru, Config.local.friends_list.en)) and remove
        except ValueError:
            return False


class IsBackToCourses(BoundFilter):
    key = 'is_back_to_courses'

    def __init__(self, is_back_to_courses):
        self.is_back_to_courses = is_back_to_courses

    async def check(self, callback_query: CallbackQuery) -> bool:
        raws = callback_query.data.split('.')
        return len(raws) == 2 and raws[0] == 'back' and raws[1] == 'courses'


class IsBackToCampusesFromCourses(BoundFilter):
    key = 'is_back_to_campuses_from_courses'

    def __init__(self, is_back_to_campuses_from_courses):
        self.is_back_to_campuses_from_courses = is_back_to_campuses_from_courses

    async def check(self, callback_query: CallbackQuery) -> bool:
        raws = callback_query.data.split('.')
        return len(raws) == 3 and raws[0] == 'back' and raws[1] == 'courses'


class IsBackToCampusesFromLocations(BoundFilter):
    key = 'is_back_to_campuses_from_locations'

    def __init__(self, is_back_to_campuses_from_locations):
        self.is_back_to_campuses_from_locations = is_back_to_campuses_from_locations

    async def check(self, callback_query: CallbackQuery) -> bool:
        raws = callback_query.data.split('.')
        return len(raws) == 2 and raws[0] == 'back' and raws[1] == 'locations'
