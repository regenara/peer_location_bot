from contextlib import suppress

from aiogram.types import Message
from aiogram.utils.exceptions import MessageToDeleteNotFound
from aiogram.utils.exceptions import MessageToEditNotFound

from data.config import LOCALIZATION_TEXTS
from handlers.throttling import throttled
from misc import dp
from misc import mongo
from models.user import User
from services.keyboards import pagination_keyboard
from services.keyboards import peer_keyboard
from utils.helpers import nickname_valid
from utils.helpers import nicknames_separation
from utils.text_compile import host_data_compile
from utils.text_compile import peer_data_compile
from utils.text_compile import peer_feedbacks_compile
from utils.text_compile import peer_locations_compile


@dp.message_handler(lambda message: message.text.startswith('?') and len(message.text) > 2)
@dp.throttled(throttled, rate=5)
async def peer_locations(message: Message):
    user_id = message.from_user.id
    data = await mongo.find('users', {'user_id': user_id})
    user = User.from_dict(data)
    peer_locations_locale = LOCALIZATION_TEXTS['last_locations'][user.lang]
    nickname = message.text[1:].lower().strip().replace('@', '')
    if not nickname_valid(nickname):
        if len(nickname) > 20:
            nickname = f'{nickname[:20]}...'
        locations_text = peer_locations_locale['not_found'].format(nickname=nickname.replace("<", "&lt"))
        await message.answer(locations_text)
    else:
        message = await message.answer(LOCALIZATION_TEXTS['wait'][user.lang])
        peer_locations_data = await peer_locations_compile(nickname, peer_locations_locale)
        keyboard = pagination_keyboard('locations', peer_locations_data['count'], nickname, 10, 4)
        locations_text = peer_locations_data['text']
        with suppress(MessageToDeleteNotFound):
            await message.delete()
        await message.answer(locations_text, reply_markup=keyboard)


@dp.message_handler(lambda message: message.text.startswith('!') and len(message.text) > 2)
@dp.throttled(throttled, rate=5)
async def peer_feedbacks(message: Message):
    user_id = message.from_user.id
    data = await mongo.find('users', {'user_id': user_id})
    user = User.from_dict(data)
    peer_feedbacks_locale = LOCALIZATION_TEXTS['feedbacks'][user.lang]
    nickname = message.text[1:].lower().strip().replace('@', '')
    if not nickname_valid(nickname):
        if len(nickname) > 20:
            nickname = f'{nickname[:20]}...'
        feedbacks_text = peer_feedbacks_locale['not_found'].format(nickname=nickname.replace("<", "&lt"))
        await message.answer(feedbacks_text)
    else:
        message = await message.answer(LOCALIZATION_TEXTS['wait'][user.lang])
        peer_feedbacks_data = await peer_feedbacks_compile(nickname, peer_feedbacks_locale)
        feedbacks_text = peer_feedbacks_data['text']
        keyboard = pagination_keyboard('feedbacks', peer_feedbacks_data['count'], nickname, 5, 9)
        with suppress(MessageToDeleteNotFound):
            await message.delete()
        await message.answer(feedbacks_text, disable_web_page_preview=True, reply_markup=keyboard)


@dp.message_handler(lambda message: message.text.startswith('#') and len(message.text) > 2)
@dp.throttled(throttled, rate=5)
async def host_data_(message: Message):
    user_id = message.from_user.id
    data = await mongo.find('users', {'user_id': user_id})
    user = User.from_dict(data)
    host_data_locale = LOCALIZATION_TEXTS['host'][user.lang]
    host = message.text[1:].lower().strip()
    if not nickname_valid(host):
        if len(host) > 20:
            host = f'{host[:20]}...'
        host_text = host_data_locale['not_found'].format(nickname=host.replace("<", "&lt"))
        await message.answer(host_text)
    else:
        message = await message.answer(LOCALIZATION_TEXTS['wait'][user.lang])
        peer_data_locale = LOCALIZATION_TEXTS['user_info'][user.lang]
        host_data = await host_data_compile(host, host_data_locale, peer_data_locale, user.avatar)
        keyboard = None
        if not host_data.get('error'):
            peer_kb = peer_keyboard([host_data['peer']], user.friends, user.notifications)
            keyboard = pagination_keyboard('host', 1, host_data['host'], 0, 3,
                                           keyboard=peer_kb, extra=host_data['campus'])
        with suppress(MessageToDeleteNotFound):
            await message.delete()
        await message.answer(host_data['text'], reply_markup=keyboard)


@dp.message_handler(lambda message: len(message.text.split()) == 1)
@dp.throttled(throttled, rate=5)
async def peer_data_(message: Message):
    user_id = message.from_user.id
    data = await mongo.find('users', {'user_id': user_id})
    user = User.from_dict(data)
    peer_data_locale = LOCALIZATION_TEXTS['user_info'][user.lang]
    nickname = message.text.lower().replace('@', '').split()[0]
    keyboard = None
    if not nickname_valid(nickname):
        if len(nickname) > 20:
            nickname = f'{nickname[:20]}...'
        peer_text = peer_data_locale['not_found'].format(nickname=nickname.replace("<", "&lt"))
    else:
        peer_data = await peer_data_compile(nickname, peer_data_locale, True, user.avatar)
        if not peer_data.get('error'):
            keyboard = peer_keyboard([nickname], user.friends, user.notifications)
        peer_text = peer_data['text']
    await message.answer(peer_text, reply_markup=keyboard)


@dp.message_handler()
@dp.throttled(throttled, rate=10)
async def peers_data(message: Message):
    user_id = message.from_user.id
    data = await mongo.find('users', {'user_id': user_id})
    user = User.from_dict(data)
    peer_data_locale = LOCALIZATION_TEXTS['user_info'][user.lang]
    nicknames = message.text.lower().replace('@', '').split()[:5]
    peer_nicknames, bad_nicknames = await nicknames_separation(nicknames)
    message = await message.answer(LOCALIZATION_TEXTS['wait'][user.lang])
    texts = []
    peers = []
    for nickname in peer_nicknames:
        peer_data = await peer_data_compile(nickname, peer_data_locale, False)
        if not peer_data.get('error'):
            peers.append(nickname)
        texts.append(peer_data['text'])
        text = '\n\n'.join(texts)
        with suppress(MessageToEditNotFound):
            await message.edit_text(text)
    for nickname in bad_nicknames:
        peer_text = peer_data_locale['not_found'].format(nickname=nickname.replace("<", "&lt"))
        texts.append(peer_text)
    text = '\n\n'.join(texts)
    with suppress(MessageToDeleteNotFound):
        await message.delete()
    await message.answer(text, reply_markup=peer_keyboard(peers, user.friends, user.notifications))
