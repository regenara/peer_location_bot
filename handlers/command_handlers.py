from aiogram.types import Message

from misc import bot
from misc import dp
from misc import mongo
from data.config import localization_texts
from services.keyboards import intra_users_keyboard
from services.keyboards import language_keyboard
from services.text_compile import get_user_info


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
    friends_count = len(friends)
    head = f'<b>{localization_texts["friends"][lang]["list"]}</b>'
    keyboard = None
    if not friends_count:
        text = localization_texts['friends'][lang]['no_friends']
    elif friends_count == 1:
        text, nickname = await get_user_info(friends[0], lang, True)
        text = f'{head}\n\n{text}'
        keyboard = intra_users_keyboard(friends, friends, notifications)
    else:
        text = localization_texts['wait'][lang]
    message_id = (await bot.send_message(user_id, text, reply_markup=keyboard)).message_id
    if friends_count > 1:
        texts = ['']
        for i, friend in enumerate(friends, 1):
            texts[0] = f'{head} ({i}/{friends_count})'
            text, nickname = await get_user_info(friend, lang, False)
            texts.append(text)
            text = '\n\n'.join(texts)
            await bot.edit_message_text(text, user_id, message_id)
        texts[0] = head
        text = '\n\n'.join(texts)
        await bot.delete_message(user_id, message_id)
        await bot.send_message(user_id, text, reply_markup=intra_users_keyboard(friends, friends, notifications))


@dp.message_handler(commands=['about'])
async def friends_info(message: Message):
    await message.answer('<a href="https://github.com/JakeBV/peer_location_bot">Source</a>')
