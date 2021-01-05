from aiogram.types import CallbackQuery

from misc import bot
from misc import dp
from misc import mongo
from data.config import localization_texts
from services.keyboards import avatar_keyboard
from services.keyboards import results_count_keyboard
from services.keyboards import intra_users_keyboard
from services.keyboards import menu_keyboard
from services.text_compile import friends_list_normalization


@dp.callback_query_handler(lambda callback: callback.data in ('ru', 'en'))
async def intra_user_avatar(callback_query: CallbackQuery):
    new_lang = callback_query.data
    user_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    await mongo.update_tg_user(user_id, {'$set': {'settings.lang': new_lang}})
    await bot.answer_callback_query(callback_query.id)
    text = localization_texts['avatar'][new_lang]
    yes_or_no = localization_texts['yes_or_no'][new_lang]
    yes, no = yes_or_no['yes'], yes_or_no['no']
    await bot.edit_message_text(text, user_id, message_id, reply_markup=avatar_keyboard(yes, no))


@dp.callback_query_handler(lambda callback: callback.data in ('yes', 'no'))
async def feedbacks_count(callback_query: CallbackQuery):
    yes_or_no = callback_query.data == 'yes'
    user_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    lang = await mongo.get_lang(user_id)
    await mongo.update_tg_user(user_id, {'$set': {'settings.avatar': yes_or_no}})
    await bot.answer_callback_query(callback_query.id)
    text = localization_texts['results_count'][lang]
    await bot.edit_message_text(text, user_id, message_id, reply_markup=results_count_keyboard())


@dp.callback_query_handler(lambda callback: callback.data.isdigit())
async def saving_settings(callback_query: CallbackQuery):
    results_count = int(callback_query.data)
    user_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    lang = await mongo.get_lang(user_id)
    await mongo.update_tg_user(user_id, {'$set': {'settings.results_count': results_count}})
    await bot.answer_callback_query(callback_query.id)
    text = localization_texts['saving_settings'][lang]
    text += localization_texts["help"][lang]
    await bot.delete_message(user_id, message_id)
    await bot.send_message(user_id, text, reply_markup=menu_keyboard(lang))


@dp.callback_query_handler(lambda callback: callback.data.split('=')[0] in ('on', 'off'))
async def switch_notification(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    switch, nickname = callback_query.data.split('=')
    action = 'pull'
    if switch == 'on':
        action = 'addToSet'
    buttons = callback_query.message.reply_markup.inline_keyboard
    count = await mongo.get_count(user_id, 'notifications')
    lang = await mongo.get_lang(user_id)
    if action == 'addToSet' and count == 10:
        alert_text = localization_texts['notifications'][lang]['count']
        await bot.answer_callback_query(callback_query.id, alert_text, show_alert=True)
    else:
        intra_users = [button.callback_data.split('=')[1] for row in buttons for button in row][::2]
        await mongo.update_tg_user(user_id, {f'${action}': {'notifications': nickname}})
        await mongo.update_intra_user(nickname, {f'${action}': {'stalkers': user_id}})
        user_data = await mongo.find_tg_user(user_id)
        friends = user_data['friends']
        notifications = user_data['notifications']
        alert_text = eval(localization_texts['notifications'][lang][switch])
        await bot.answer_callback_query(callback_query.id, alert_text, show_alert=True)
        keyboard = intra_users_keyboard(intra_users, friends, notifications)
        await bot.edit_message_reply_markup(user_id, message_id, reply_markup=keyboard)


@dp.callback_query_handler(is_friends_list=True)
async def friends_list(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    nickname = callback_query.data.split('=')[1]
    buttons = callback_query.message.reply_markup.inline_keyboard
    lang = await mongo.get_lang(user_id)
    message_text = callback_query.message.text
    get_intra_users = [button.callback_data.split('=')[1] for row in buttons for button in row][::2]
    intra_users = [intra_user for intra_user in get_intra_users if intra_user != nickname]
    await mongo.update_tg_user(user_id, {f'$pull': {'friends': nickname}})
    user_data = await mongo.find_tg_user(user_id)
    friends = user_data['friends']
    notifications = user_data['notifications']
    text = friends_list_normalization(message_text, intra_users, lang)
    alert_text = eval(localization_texts['friends_actions'][lang]['pull'])
    await bot.answer_callback_query(callback_query.id, alert_text, show_alert=True)
    keyboard = intra_users_keyboard(intra_users, friends, notifications)
    await bot.edit_message_text(text, user_id, message_id, reply_markup=keyboard)


@dp.callback_query_handler(lambda callback: callback.data.split('=')[0] in ('addToSet', 'pull'))
async def friends_actions(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    message_id = callback_query.message.message_id
    action, nickname = callback_query.data.split('=')
    buttons = callback_query.message.reply_markup.inline_keyboard
    count = await mongo.get_count(user_id, 'friends')
    lang = await mongo.get_lang(user_id)
    if action == 'addToSet' and count == 20:
        alert_text = localization_texts['friends_actions'][lang]['count']
        await bot.answer_callback_query(callback_query.id, alert_text, show_alert=True)
    else:
        intra_users = [button.callback_data.split('=')[1] for row in buttons for button in row][::2]
        await mongo.update_tg_user(user_id, {f'${action}': {'friends': nickname}})
        user_data = await mongo.find_tg_user(user_id)
        friends = user_data['friends']
        notifications = user_data['notifications']
        alert_text = eval(localization_texts['friends_actions'][lang][action])
        await bot.answer_callback_query(callback_query.id, alert_text, show_alert=True)
        keyboard = intra_users_keyboard(intra_users, friends, notifications)
        await bot.edit_message_reply_markup(user_id, message_id, reply_markup=keyboard)
