from typing import Tuple

from aiogram.types import (CallbackQuery,
                           Message)

from bot import dp
from config import Config
from db_models.campuses import Campus
from db_models.peers import Peer
from db_models.users import User
from services.keyboards import menu_keyboard


@dp.callback_query_handler(state='throttler')
async def callback_throttler(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    *_, user = user_data
    await callback_query.answer(Config.local.antiflood.get(user.language))


@dp.message_handler(state='throttler')
async def message_throttler(message: Message, user_data: Tuple[Campus, Peer, User]):
    *_, user = user_data
    await message.answer(Config.local.antiflood.get(user.language), reply_markup=menu_keyboard(user.language))
