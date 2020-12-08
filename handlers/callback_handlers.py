from aiogram import types

from misc import bot
from misc import dp
from misc import mongo
from config import localization_texts
from keyboards import avatar_keyboard


@dp.callback_query_handler(lambda callback: callback.data in ('ru', 'en'))
async def intra_user_avatar(callback_query: types.CallbackQuery):
    new_lang = callback_query.data
    user_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    await mongo.update(user_id, {'$set': {'settings.lang': new_lang}})
    await bot.answer_callback_query(callback_query.id)
    text = localization_texts['avatar'][new_lang]
    yes_or_no = localization_texts['yes_or_no'][new_lang]
    await bot.edit_message_text(text, user_id, message_id, reply_markup=avatar_keyboard(yes_or_no['yes'],
                                                                                        yes_or_no['no']))


@dp.callback_query_handler(lambda callback: callback.data in ('yes', 'no'))
async def saving_settings(callback_query: types.CallbackQuery):
    yes_or_no = callback_query.data == 'yes'
    user_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    lang = (await mongo.find_tg_user(user_id))['settings']['lang']
    await mongo.update(user_id, {'$set': {'settings.avatar': yes_or_no}})
    await bot.answer_callback_query(callback_query.id)
    text = localization_texts['saving_settings'][lang]
    text += localization_texts["help"][lang]
    await bot.edit_message_text(text, user_id, message_id)


@dp.callback_query_handler(lambda callback: callback.split('=')[0] in ('on', 'off'))
async def switch_notification(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    switch, login = callback_query.data.split('=')
    on = True
    if switch == 'on':
        on = False
    await mongo.update(user_id, {'$set': {f'friends.{login}': on}})
