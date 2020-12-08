from aiogram import types

from keyboards import intra_users_keyboard
from misc import dp
from misc import mongo
from text_compile import get_last_locations
from text_compile import get_users_info


@dp.message_handler(text_startswith=['? '])
async def intra_user_locations(message: types.Message):
    user_id = message.from_user.id
    nickname = message.text[2:].lower().strip()
    user_data = (await mongo.find_tg_user(user_id))['settings']
    lang = user_data['lang']
    text = get_last_locations(nickname, lang)
    await message.answer(text)


@dp.message_handler()
async def intra_users_info(message: types.Message):
    user_id = message.from_user.id
    user_data = await mongo.find_tg_user(user_id)
    lang = user_data['settings']['lang']
    avatar = user_data['settings']['avatar']
    friends = user_data['friends']
    users_info = get_users_info(message.text, lang, avatar, friends)
    text = users_info['text']
    intra_users = users_info['intra_users']
    await message.answer(text, reply_markup=intra_users_keyboard(intra_users, friends) if intra_users else None)
