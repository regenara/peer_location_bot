from contextlib import suppress

from aiogram.types import CallbackQuery
from aiogram.utils.exceptions import MessageToDeleteNotFound
from aiogram.utils.exceptions import MessageCantBeDeleted

from data.config import LOCALIZATION_TEXTS
from misc import dp
from misc import mongo
from models.user import User
from services.keyboards import menu_keyboard
from services.keyboards import peer_keyboard
from services.keyboards import settings_keyboard
from utils.helpers import friends_list_normalization
from utils.helpers import keyboard_normalize


@dp.callback_query_handler(lambda callback: callback.data in ('ru', 'en'), state='*')
async def peer_avatar(callback_query: CallbackQuery):
    new_lang = callback_query.data
    user_id = callback_query.from_user.id
    await mongo.update('users', {'user_id': user_id}, 'set', {'settings.lang': new_lang})
    await callback_query.answer()
    text = LOCALIZATION_TEXTS['avatar'][new_lang]
    yes = LOCALIZATION_TEXTS['yes_or_no'][new_lang]['yes']
    no = LOCALIZATION_TEXTS['yes_or_no'][new_lang]['no']
    await callback_query.answer()
    await callback_query.message.edit_text(text, reply_markup=settings_keyboard('avatar', yes, no))


@dp.callback_query_handler(lambda callback: callback.data in ('yes_avatar', 'no_avatar'), state='*')
async def save_settings(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    yes_or_no = callback_query.data == 'yes_avatar'
    data = await mongo.update('users', {'user_id': user_id}, 'set', {'settings.avatar': yes_or_no})
    user = User.from_dict(data)
    await callback_query.answer()
    if callback_query.from_user.username:
        text = LOCALIZATION_TEXTS['anon'][user.lang]
        yes = LOCALIZATION_TEXTS['yes_or_no'][user.lang]['yes']
        no = LOCALIZATION_TEXTS['yes_or_no'][user.lang]['no']
        await callback_query.answer()
        await callback_query.message.edit_text(text, reply_markup=settings_keyboard('anon', yes, no))
    else:
        text = LOCALIZATION_TEXTS['saving_settings'][user.lang]
        text += LOCALIZATION_TEXTS['help'][user.lang]
        await callback_query.answer()
        with suppress(MessageToDeleteNotFound, MessageCantBeDeleted):
            await callback_query.message.delete()
        await callback_query.message.answer(text, reply_markup=menu_keyboard(user.lang))


@dp.callback_query_handler(lambda callback: callback.data in ('yes_anon', 'no_anon'), state='*')
async def anon_settings(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    yes_or_no = callback_query.data == 'no_anon'
    data = await mongo.update('users', {'user_id': user_id}, 'set', {'settings.anon': yes_or_no})
    user = User.from_dict(data)
    text = LOCALIZATION_TEXTS['saving_settings'][user.lang]
    text += LOCALIZATION_TEXTS['help'][user.lang]
    await callback_query.answer()
    with suppress(MessageToDeleteNotFound, MessageCantBeDeleted):
        await callback_query.message.delete()
    await callback_query.message.answer(text, reply_markup=menu_keyboard(user.lang))


@dp.callback_query_handler(lambda callback: callback.data.split('=')[0] in ('on', 'off'), state='*')
async def switch_notification(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    switch, nickname = callback_query.data.split('=')
    operator = 'pull'
    if switch == 'on':
        operator = 'addToSet'
    buttons = callback_query.message.reply_markup.inline_keyboard
    data = await mongo.find('users', {'user_id': user_id})
    user = User.from_dict(data)
    if operator == 'addToSet' and user.notifications_count == 10:
        alert_text = LOCALIZATION_TEXTS['notifications'][user.lang]['count']
        await callback_query.answer(alert_text, show_alert=True)
    else:
        data = await mongo.update('users', {'user_id': user_id}, operator,
                                  {'notifications': nickname}, return_document=True)
        await mongo.update('peers', {'nickname': nickname}, operator, {'stalkers': user_id}, upsert=True)
        user = User.from_dict(data)
        alert_text = LOCALIZATION_TEXTS['notifications'][user.lang][switch].format(nickname=nickname)
        await callback_query.answer(alert_text, show_alert=True)
        await callback_query.message.edit_reply_markup(keyboard_normalize(buttons, user.friends, user.notifications))


@dp.callback_query_handler(is_remove_friend=True, state='*')
async def friends_list(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    nickname = callback_query.data.split('=')[1]
    buttons = callback_query.message.reply_markup.inline_keyboard
    message_text = callback_query.message.text
    get_friends = [button.callback_data.split('=')[1] for row in buttons for button in row][::2]
    friends = [friend for friend in get_friends if friend != nickname]
    data = await mongo.update('users', {'user_id': user_id}, 'pull',
                              {'friends': nickname}, return_document=True)
    user = User.from_dict(data)
    text = friends_list_normalization(message_text, friends)
    if not text:
        text = LOCALIZATION_TEXTS['friends'][user.lang]['no_friends']
    alert_text = LOCALIZATION_TEXTS['friends_actions'][user.lang]['pull'].format(nickname=nickname)
    await callback_query.answer(alert_text, show_alert=True)
    await callback_query.message.edit_text(text, reply_markup=peer_keyboard(friends, user.friends, user.notifications))


@dp.callback_query_handler(lambda callback: callback.data.split('=')[0] in ('addToSet', 'pull'), state='*')
async def friends_actions(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    operator, nickname = callback_query.data.split('=')
    buttons = callback_query.message.reply_markup.inline_keyboard
    data = await mongo.find('users', {'user_id': user_id})
    user = User.from_dict(data)
    if operator == 'addToSet' and user.friends_count == 20:
        alert_text = LOCALIZATION_TEXTS['friends_actions'][user.lang]['count']
        await callback_query.answer(alert_text, show_alert=True)
    else:
        data = await mongo.update('users', {'user_id': user_id}, operator,
                                  {'friends': nickname}, return_document=True)
        user = User.from_dict(data)
        alert_text = LOCALIZATION_TEXTS['friends_actions'][user.lang][operator].format(nickname=nickname)
        await callback_query.answer(alert_text, show_alert=True)
        await callback_query.message.edit_reply_markup(keyboard_normalize(buttons, user.friends, user.notifications))
