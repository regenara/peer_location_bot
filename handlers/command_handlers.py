import asyncio
from contextlib import suppress

from aiogram.types import Message
from aiogram.utils.exceptions import ChatNotFound
from aiogram.utils.exceptions import BotBlocked
from aiogram.utils.exceptions import UserDeactivated

from handlers.throttling import throttled
from misc import bot
from misc import dp
from misc import mongo
from data.config import localization_texts
from services.keyboards import intra_users_keyboard
from services.keyboards import language_keyboard
from services.keyboards import menu_keyboard
from services.text_compile import get_user_info


@dp.message_handler(is_settings=True)
async def send_welcome(message: Message):
    user_id = message.from_user.id
    lang = await mongo.get_lang(user_id)
    text = localization_texts['language'][lang]
    await message.answer(text, reply_markup=language_keyboard())


@dp.message_handler(is_help=True)
async def send_help(message: Message):
    user_id = message.from_user.id
    lang = await mongo.get_lang(user_id)
    text = localization_texts['help'][lang]
    await message.answer(text)


@dp.message_handler(is_no_friends=True)
async def no_friends(message: Message):
    user_id = message.from_user.id
    lang = await mongo.get_lang(user_id)
    text = localization_texts['friends'][lang]['no_friends']
    await message.answer(text)


@dp.message_handler(is_alone_friend=True)
@dp.throttled(throttled, rate=3)
async def alone_friend(message: Message):
    user_id = message.from_user.id
    user_data = await mongo.find_tg_user(user_id)
    lang = user_data['settings']['lang']
    friends = user_data['friends']
    notifications = user_data['notifications']
    text, nickname = await get_user_info(friends[0], lang, True)
    text = f'<b>{localization_texts["friends"][lang]["list"]}</b>\n\n{text}'
    keyboard = intra_users_keyboard(friends, friends, notifications)
    await message.answer(text, reply_markup=keyboard)


@dp.message_handler(is_friends=True)
@dp.throttled(throttled, rate=20)
async def friends_info(message: Message):
    user_id = message.from_user.id
    user_data = await mongo.find_tg_user(user_id)
    lang = user_data['settings']['lang']
    friends = user_data['friends']
    notifications = user_data['notifications']
    friends_count = len(friends)
    head = f'<b>{localization_texts["friends"][lang]["list"]}</b>'
    text = localization_texts['wait'][lang]
    message_id = (await bot.send_message(user_id, text)).message_id
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


@dp.message_handler(is_about=True)
async def about(message: Message):
    await message.answer('<a href="https://github.com/JakeBV/peer_location_bot">Source</a>')


@dp.message_handler(is_donate=True)
async def donate(message: Message):
    await message.answer('<a href="https://qiwi.com/payment/form/99999?extra[%27accountType%27]=nickname&extra'
                         '[%27account%27]=jakebv&amount=150&currency=RUB">Donate for coffee</a>')


@dp.message_handler(is_mailing=True)
async def mailing(message: Message):
    text = message.text[2:]
    cursor = await mongo.get_tg_users()
    documents = await cursor.to_list(length=100)
    while documents:
        for document in documents:
            user_id = document['user_id']
            lang = document['settings']['lang']
            with suppress(ChatNotFound, BotBlocked, UserDeactivated):
                await bot.send_message(user_id, text, reply_markup=menu_keyboard(lang))
            await asyncio.sleep(0.1)
        documents = await cursor.to_list(length=100)
    await message.answer('Готово!')
