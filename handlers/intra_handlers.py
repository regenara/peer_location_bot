from aiogram import types

from services.keyboards import intra_users_keyboard
from misc import dp
from misc import mongo
from services.text_compile import get_last_locations
from services.text_compile import get_users_info


@dp.message_handler(text_startswith=['? '])
async def intra_user_locations(message: types.Message):
    user_id = message.from_user.id
    nickname = message.text[2:].lower().strip()
    lang = await mongo.get_lang(user_id)
    text = get_last_locations(nickname, lang)
    await message.answer(text)


@dp.message_handler()
async def intra_users_info(message: types.Message):
    user_id = message.from_user.id
    user_data = await mongo.find_tg_user(user_id)
    lang = user_data['settings']['lang']
    avatar = user_data['settings']['avatar']
    friends = user_data['friends']
    notifications = user_data['notifications']
    users_info = await get_users_info(message.text, lang, avatar)
    text = users_info['text']
    intra_users = users_info['intra_users']
    keyboard = intra_users_keyboard(intra_users, friends, notifications) if intra_users else None
    await message.answer(text, reply_markup=keyboard)
