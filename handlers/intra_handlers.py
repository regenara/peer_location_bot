from contextlib import suppress

from aiogram.types import Message
from aiogram.utils.exceptions import MessageToEditNotFound
from aiogram.utils.exceptions import MessageToDeleteNotFound

from data.config import localization_texts
from handlers.throttling import throttled
from misc import bot
from misc import dp
from misc import mongo
from services.keyboards import intra_users_keyboard
from services.text_compile import get_last_locations
from services.text_compile import get_user_feedbacks
from services.text_compile import get_user_info
from services.utils import safe_split_text


@dp.message_handler(text_startswith=['?'])
@dp.throttled(throttled, rate=3)
async def intra_user_locations(message: Message):
    user_id = message.from_user.id
    nickname = message.text[1:].lower().strip().replace('@', '')
    lang = await mongo.get_lang(user_id)
    text = get_last_locations(nickname, lang)
    await message.answer(text)


@dp.message_handler(text_startswith=['!'])
@dp.throttled(throttled, rate=3)
async def intra_user_feedbacks(message: Message):
    user_id = message.from_user.id
    nickname = message.text[1:].lower().strip().replace('@', '')
    lang = await mongo.get_lang(user_id)
    results_count = await mongo.get_results_count(user_id)
    text = await get_user_feedbacks(nickname, lang, results_count)
    texts = safe_split_text(text)
    for text in texts:
        await message.answer(text, disable_web_page_preview=True)


@dp.message_handler(is_single_request=True)
@dp.throttled(throttled, rate=3)
async def single_request(message: Message):
    user_id = message.from_user.id
    user_data = await mongo.find_tg_user(user_id)
    lang = user_data['settings']['lang']
    avatar = user_data['settings']['avatar']
    friends = user_data['friends']
    notifications = user_data['notifications']
    nickname = message.text.strip().lower()
    text, is_nickname = await get_user_info(nickname, lang, True, avatar)
    keyboard = None
    if is_nickname:
        keyboard = intra_users_keyboard([nickname], friends, notifications)
    await message.answer(text, reply_markup=keyboard)


@dp.message_handler()
@dp.throttled(throttled, rate=10)
async def intra_users_info(message: Message):
    user_id = message.from_user.id
    user_data = await mongo.find_tg_user(user_id)
    lang = user_data['settings']['lang']
    friends = user_data['friends']
    notifications = user_data['notifications']
    get_nicknames = message.text.lower().split()
    nicknames = list(dict.fromkeys(get_nicknames))[:5]
    text = localization_texts['wait'][lang]
    message_id = (await bot.send_message(user_id, text)).message_id
    texts = []
    intra_users = []
    for nickname in nicknames:
        text, is_nickname = await get_user_info(nickname, lang, False)
        texts.append(text)
        if is_nickname:
            intra_users.append(is_nickname)
        text = '\n\n'.join(texts)
        with suppress(MessageToEditNotFound):
            await bot.edit_message_text(text, user_id, message_id)
    with suppress(MessageToDeleteNotFound):
        await bot.delete_message(user_id, message_id)
    await bot.send_message(user_id, text, reply_markup=intra_users_keyboard(intra_users, friends, notifications))
