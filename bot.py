from aiogram import Bot, Dispatcher, executor, types

import config
from config import localization_texts
import mongo_db
from keyboards import language_keyboard, avatar_keyboard
from text_generator import text_compile, get_last_locations


bot = Bot(token=config.api_token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    find_settings = await mongo_db.find_tg_user(user_id)
    lang = message.from_user.language_code
    if find_settings is None:
        await mongo_db.db_fill(user_id, lang)
    else:
        lang = find_settings['settings']['lang']
    text = localization_texts['language'][lang]
    await message.answer(text, reply_markup=language_keyboard())


@dp.message_handler(commands=['help'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    lang = (await mongo_db.find_tg_user(user_id))['settings']['lang']
    text = localization_texts['help'][lang]
    await message.answer(text)


@dp.message_handler(text_startswith=['? '])
async def user_locations(message: types.Message):
    user_id = message.from_user.id
    nickname = message.text[2:].lower().strip()
    user_data = (await mongo_db.find_tg_user(user_id))['settings']
    lang = user_data['lang']
    text = get_last_locations(nickname, lang)
    await message.answer(text)


@dp.callback_query_handler(lambda callback: callback.data in ('ru', 'en'))
async def user_timezone(callback_query: types.CallbackQuery):
    new_lang = callback_query.data
    user_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    await mongo_db.update(user_id, {'$set': {'settings.lang': new_lang}})
    await bot.answer_callback_query(callback_query.id)
    text = localization_texts['avatar'][new_lang]
    yes_or_no = localization_texts['yes_or_no'][new_lang]
    await bot.edit_message_text(text, user_id, message_id, reply_markup=avatar_keyboard(yes_or_no['yes'],
                                                                                        yes_or_no['no']))

"""
@dp.callback_query_handler(lambda callback: '+' in callback.data or '-' in callback.data)
async def user_avatar(callback_query: types.CallbackQuery):
    utc = callback_query.data
    user_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    lang = (await mongo_db.find_tg_user(user_id))['settings']['lang']
    await mongo_db.update(user_id, {'$set': {'settings.timezone': utc}})
    await bot.answer_callback_query(callback_query.id)
    text = eval(localization_texts['avatar'][lang])
    yes_or_no = localization_texts['yes_or_no'][lang]
    await bot.edit_message_text(text, user_id, message_id, reply_markup=avatar_keyboard(yes_or_no['yes'],
                                                                                        yes_or_no['no']))"""


@dp.callback_query_handler(lambda callback: callback.data in ('yes', 'no'))
async def saving_settings(callback_query: types.CallbackQuery):
    yes_or_no = callback_query.data == 'yes'
    user_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    lang = (await mongo_db.find_tg_user(user_id))['settings']['lang']
    await mongo_db.update(user_id, {'$set': {'settings.avatar': yes_or_no}})
    await bot.answer_callback_query(callback_query.id)
    text = localization_texts['saving_settings'][lang]
    text += localization_texts["help"][lang]
    await bot.edit_message_text(text, user_id, message_id)



@dp.message_handler()
async def echo(message: types.Message):
    text = text_compile(message.text, 'en', True)
    await message.answer(text['text'])


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
