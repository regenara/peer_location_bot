from typing import Tuple

from aiogram.types import (CallbackQuery,
                           Message)

from bot import (dp,
                 bot)
from config import Config
from db_models.campuses import Campus
from db_models.peers import Peer
from db_models.users import User
from services.keyboards import (auth_keyboard,
                                menu_keyboard)
from services.states import States


@dp.callback_query_handler(is_unauthorized=True, state='*')
async def welcome_callback(callback_query: CallbackQuery):
    await dp.current_state(user=callback_query.from_user.id).set_state(States.AUTH)
    language_code = callback_query.from_user.language_code if \
        callback_query.from_user.language_code in ('ru', 'en') else 'en'
    user_id = callback_query.from_user.id
    message = await bot.send_message(user_id, '🗿')
    await message.edit_text(Config.local.need_auth.get(language_code),
                            reply_markup=auth_keyboard(message_id=message.message_id, user_id=user_id,
                                                       language_code=language_code))


@dp.message_handler(is_unauthorized=True, state='*')
async def welcome_command(message: Message):
    await dp.current_state(user=message.from_user.id).set_state(States.AUTH)
    language_code = message.from_user.language_code if message.from_user.language_code in ('ru', 'en') else 'en'
    user_id = message.from_user.id
    message = await message.answer('🗿')
    await message.edit_text(Config.local.need_auth.get(language_code),
                            reply_markup=auth_keyboard(message_id=message.message_id, user_id=user_id,
                                                       language_code=language_code))


@dp.callback_query_handler(state='throttler')
async def callback_throttler(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    *_, user = user_data
    await callback_query.answer(Config.local.antiflood.get(user.language))


@dp.message_handler(state='throttler')
async def message_throttler(message: Message, user_data: Tuple[Campus, Peer, User]):
    *_, user = user_data
    await message.answer(Config.local.antiflood.get(user.language), reply_markup=menu_keyboard(user.language))

