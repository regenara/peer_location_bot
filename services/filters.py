from aiogram.dispatcher.filters.filters import BoundFilter
from aiogram.types import CallbackQuery

from data.config import localization_texts
import misc


class IsFriendsList(BoundFilter):
    key = 'is_friends_list'

    def __init__(self, is_friends_list):
        self.is_friends_lists = is_friends_list

    async def check(self, callback_query: CallbackQuery):
        user_id = callback_query.from_user.id
        message_text = callback_query.message.text
        remove = callback_query.data.split('=')[0] == 'pull'
        lang = await misc.mongo.get_lang(user_id)
        return message_text[:message_text.index('\n')] == localization_texts['friends'][lang]['list'] and remove
