from aiogram import types

from misc import dp
from misc import mongo
from config import localization_texts
from keyboards import language_keyboard


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    find_settings = await mongo.find_tg_user(user_id)
    lang = message.from_user.language_code
    if find_settings is None:
        await mongo.db_fill(user_id, lang)
    else:
        lang = find_settings['settings']['lang']
    text = localization_texts['language'][lang]
    await message.answer(text, reply_markup=language_keyboard())


@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    user_id = message.from_user.id
    lang = (await mongo.find_tg_user(user_id))['settings']['lang']
    text = localization_texts['help'][lang]
    await message.answer(text)
