from aiogram.types import Message

from misc import dp
from misc import mongo
from data.config import localization_texts
from services.keyboards import intra_users_keyboard
from services.keyboards import language_keyboard
from services.text_compile import get_users_info


@dp.message_handler(commands=['start'])
async def send_welcome(message: Message):
    user_id = message.from_user.id
    lang = await mongo.get_lang(user_id)
    text = localization_texts['language'][lang]
    await message.answer(text, reply_markup=language_keyboard())


@dp.message_handler(commands=['help'])
async def send_help(message: Message):
    user_id = message.from_user.id
    lang = await mongo.get_lang(user_id)
    text = localization_texts['help'][lang]
    await message.answer(text)


@dp.message_handler(commands=['friends'])
async def friends_info(message: Message):
    user_id = message.from_user.id
    user_data = await mongo.find_tg_user(user_id)
    lang = user_data['settings']['lang']
    friends = user_data['friends']
    notifications = user_data['notifications']
    required_users = user_data['friends']
    users_info = await get_users_info(required_users, lang)
    text = users_info['text']
    if not text:
        text = localization_texts['friends'][lang]['no_friends']
    else:
        text = f'<b>{localization_texts["friends"][lang]["list"]}\n\n</b>' + text
    intra_users = users_info['intra_users']
    await message.answer(text, reply_markup=intra_users_keyboard(intra_users, friends, notifications))


@dp.message_handler(commands=['about'])
async def friends_info(message: Message):
    await message.answer('<a href="https://github.com/JakeBV/where_is_the_peer_bot">Source</a>')
