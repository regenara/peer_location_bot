from datetime import datetime
from pytz import timezone

from aiogram.dispatcher.filters.filters import BoundFilter
from aiogram.types import CallbackQuery
from aiogram.types import Message

from data.config import ADMIN
from data.config import LOCALIZATION_TEXTS
from misc import dp
from misc import mongo
from models.user import User
from services.states import States


class IsStart(BoundFilter):
    key = 'is_start'

    def __init__(self, is_start):
        self.is_start = is_start

    async def check(self, message: Message) -> dict:
        user_id = message.from_user.id
        username = message.from_user.username
        text = message.text
        menu = LOCALIZATION_TEXTS['menu']
        menu_texts = [menu[key]['settings'] for key in menu]
        data = await mongo.find('users', {'user_id': user_id})
        if not data:
            user_data = {'user': None}
        else:
            user = User.from_dict(data)
            if user.username != username:
                await mongo.update('users', {'user_id': user_id}, 'set', {'username': username})
            if not user.nickname:
                user_data = {'user': None}
            else:
                user_data = {'user': user}
        if text == '/start' or text in menu_texts or not user_data['user']:
            return user_data


class IsMailing(BoundFilter):
    key = 'is_mailing'

    def __init__(self, is_mailing):
        self.is_mailing = is_mailing

    async def check(self, message: Message) -> bool:
        if message.text == '$' and message.from_user.id == ADMIN:
            await dp.current_state(user=ADMIN).set_state(States.MAILING)
            return True


class IsUpdateProjects(BoundFilter):
    key = 'is_update_projects'

    def __init__(self, is_update_projects):
        self.is_update_projects = is_update_projects

    async def check(self, message: Message) -> bool:
        if message.text == '€' and message.from_user.id == ADMIN:
            await dp.current_state(user=ADMIN).set_state(States.UPDATE_PROJECTS)
            return True


class IsIntrovert(BoundFilter):
    key = 'is_introvert'

    def __init__(self, is_introvert):
        self.is_introvert = is_introvert

    async def check(self, message: Message) -> dict:
        user_id = message.from_user.id
        text = message.text
        menu = LOCALIZATION_TEXTS['menu']
        menu_texts = [menu[key]['friends'] for key in menu]
        data = await mongo.find('users', {'user_id': user_id})
        user = User.from_dict(data)
        if (text == '/friends' or text in menu_texts) and user.friends_count < 2:
            return {'user': user}


class IsExtrovert(BoundFilter):
    key = 'is_extrovert'

    def __init__(self, is_extrovert):
        self.is_extrovert = is_extrovert

    async def check(self, message: Message) -> bool:
        text = message.text
        menu = LOCALIZATION_TEXTS['menu']
        menu_texts = [menu[key]['friends'] for key in menu]
        return text == '/friends' or text in menu_texts


class IsHelp(BoundFilter):
    key = 'is_help'

    def __init__(self, is_help):
        self.is_help = is_help

    async def check(self, message: Message) -> bool:
        text = message.text
        menu = LOCALIZATION_TEXTS['menu']
        menu_texts = [menu[key]['help'] for key in menu]
        return text == '/help' or text in menu_texts


class IsAbout(BoundFilter):
    key = 'is_about'

    def __init__(self, is_about):
        self.is_about = is_about

    async def check(self, message: Message) -> bool:
        text = message.text
        menu = LOCALIZATION_TEXTS['menu']
        menu_texts = [menu[key]['about'] for key in menu]
        return text == '/about' or text in menu_texts


class IsDonate(BoundFilter):
    key = 'is_donate'

    def __init__(self, is_donate):
        self.is_donate = is_donate

    async def check(self, message: Message) -> bool:
        text = message.text
        menu = LOCALIZATION_TEXTS['menu']
        menu_texts = [menu[key]['donate'] for key in menu]
        return text == '/donate' or text in menu_texts


class IsLocations(BoundFilter):
    key = 'is_locations'

    def __init__(self, is_locations):
        self.is_locations = is_locations

    async def check(self, message: Message) -> bool:
        text = message.text
        menu = LOCALIZATION_TEXTS['menu']
        menu_texts = [menu[key]['locations'] for key in menu]
        return text == '/locations' or text in menu_texts


class IsProjects(BoundFilter):
    key = 'is_projects'

    def __init__(self, is_projects):
        self.is_projects = is_projects

    async def check(self, message: Message) -> bool:
        text = message.text
        menu = LOCALIZATION_TEXTS['menu']
        menu_texts = [menu[key]['projects'] for key in menu]
        return text == '/projects' or text in menu_texts


class IsRemoveFriend(BoundFilter):
    key = 'is_remove_friend'

    def __init__(self, is_remove_friend):
        self.is_remove_friend = is_remove_friend

    async def check(self, callback_query: CallbackQuery) -> bool:
        user_id = callback_query.from_user.id
        message_text = callback_query.message.text
        remove = callback_query.data.split('=')[0] == 'pull'
        data = await mongo.find('users', {'user_id': user_id})
        user = User.from_dict(data)
        return message_text.split('\n')[0] == LOCALIZATION_TEXTS['friends'][user.lang]['list'] and remove
