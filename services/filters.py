from aiogram.dispatcher.filters.filters import BoundFilter
from aiogram.types import CallbackQuery
from aiogram.types import Message

from data.config import localization_texts
import misc


class IsFriends(BoundFilter):
    key = 'is_friends'

    def __init__(self, is_friends):
        self.is_friends = is_friends

    async def check(self, message: Message) -> bool:
        text = message.text
        menu = localization_texts['menu']
        menu_texts = [menu[key]['friends'] for key in menu]
        return text == '/friends' or text in menu_texts


class IsSettings(BoundFilter):
    key = 'is_settings'

    def __init__(self, is_settings):
        self.is_settings = is_settings

    async def check(self, message: Message) -> bool:
        text = message.text
        menu = localization_texts['menu']
        menu_texts = [menu[key]['settings'] for key in menu]
        return text == '/start' or text in menu_texts


class IsHelp(BoundFilter):
    key = 'is_help'

    def __init__(self, is_help):
        self.is_help = is_help

    async def check(self, message: Message) -> bool:
        text = message.text
        menu = localization_texts['menu']
        menu_texts = [menu[key]['help'] for key in menu]
        return text == '/help' or text in menu_texts


class IsAbout(BoundFilter):
    key = 'is_about'

    def __init__(self, is_about):
        self.is_about = is_about

    async def check(self, message: Message) -> bool:
        text = message.text
        menu = localization_texts['menu']
        menu_texts = [menu[key]['about'] for key in menu]
        return text == '/about' or text in menu_texts


class IsDonate(BoundFilter):
    key = 'is_donate'

    def __init__(self, is_donate):
        self.is_donate = is_donate

    async def check(self, message: Message) -> bool:
        text = message.text
        menu = localization_texts['menu']
        menu_texts = [menu[key]['donate'] for key in menu]
        return text == '/donate' or text in menu_texts


class IsFriendsList(BoundFilter):
    key = 'is_friends_list'

    def __init__(self, is_friends_list):
        self.is_friends_lists = is_friends_list

    async def check(self, callback_query: CallbackQuery) -> bool:
        user_id = callback_query.from_user.id
        message_text = callback_query.message.text
        remove = callback_query.data.split('=')[0] == 'pull'
        lang = await misc.mongo.get_lang(user_id)
        return message_text[:message_text.index('\n')] == localization_texts['friends'][lang]['list'] and remove


class IsMailing(BoundFilter):
    key = 'is_mailing'

    def __init__(self, is_mailing):
        self.is_mailing = is_mailing

    async def check(self, message: Message) -> bool:
        return message.text.startswith('$ ') and message.from_user.id == 373749366
