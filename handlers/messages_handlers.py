from contextlib import suppress
from typing import (Callable,
                    Tuple)

from aiogram.types import (InlineKeyboardMarkup,
                           Message)
from aiogram.utils.exceptions import (MessageCantBeDeleted,
                                      MessageToDeleteNotFound,
                                      MessageNotModified,
                                      MessageToEditNotFound)

from bot import dp
from config import Config
from db_models.campuses import Campus
from db_models.peers import Peer
from db_models.users import User
from db_models.users_peers import UserPeer
from services.keyboards import (pagination_keyboard,
                                peer_keyboard)
from services.states import States
from utils.text_compile import text_compile


async def action_peer(user: User, message: Message, method: Callable, action: str,
                      limit: int, stop: int) -> Tuple[str, InlineKeyboardMarkup]:
    await dp.current_state(user=user.id).set_state(States.THROTTLER)
    login = message.text[1:].lower().strip()
    message = await message.answer(Config.local.wait.get(user.language))
    await message.bot.send_chat_action(user.id, 'typing')
    text, count = await method(user=user, login=login)
    keyboard = pagination_keyboard(action=action, count=count, content=login, limit=limit, stop=stop)
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    with suppress(MessageToDeleteNotFound, MessageCantBeDeleted):
        await message.delete()
    return text, keyboard


@dp.message_handler(lambda message: message.text.startswith('@') and len(message.text) > 2, state='granted')
async def peer_data_from_username(message: Message, user_data: Tuple[Campus, Peer, User]):
    *_, user = user_data
    username = message.text[1:].lower().strip()
    login = await User.get_login_from_username(username=username)
    if not login:
        await message.answer(Config.local.not_found_username.get(user.language, username=username.replace("<", "&lt")))
    else:
        message.text = login
        await peer_data(message=message, user_data=user_data)


@dp.message_handler(lambda message: message.text.startswith('?') and len(message.text) > 2, state='granted')
async def peer_locations(message: Message, user_data: Tuple[Campus, Peer, User]):
    text, keyboard = await action_peer(user=user_data[-1], message=message, method=text_compile.peer_locations_compile,
                                       action='peer_locations_pagination', limit=10, stop=4)
    await message.answer(text, reply_markup=keyboard)


@dp.message_handler(lambda message: message.text.startswith('!') and len(message.text) > 2, state='granted')
async def peer_feedbacks(message: Message, user_data: Tuple[Campus, Peer, User]):
    text, keyboard = await action_peer(user=user_data[-1], message=message, method=text_compile.peer_feedbacks_compile,
                                       action='feedbacks_pagination', limit=5, stop=9)
    await message.answer(text, disable_web_page_preview=True, reply_markup=keyboard)


@dp.message_handler(lambda message: message.text.startswith('#') and len(message.text) > 2, state='granted')
async def host_data(message: Message, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=message.from_user.id).set_state(States.THROTTLER)
    *_, user = user_data
    host = message.text[1:].lower().strip()
    message = await message.answer(Config.local.wait.get(user.language))
    await message.bot.send_chat_action(user.id, 'typing')
    text, peer = await text_compile.host_data_compile(user=user, host=host)
    keyboard = None
    if peer:
        friends = await UserPeer.get_friends(user_id=user.id)
        observables = await UserPeer.get_observables(user_id=user.id)
        keyboard = peer_keyboard(peers=[peer], friends=friends, observables=observables, payload='host')
        keyboard = pagination_keyboard(action='host_pagination', count=1, content=host, limit=0,
                                       stop=3, keyboard=keyboard)
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    with suppress(MessageToDeleteNotFound, MessageCantBeDeleted):
        await message.delete()
    await message.answer(text, reply_markup=keyboard)


@dp.message_handler(lambda message: len(message.text.split()) == 1, state='granted')
async def peer_data(message: Message, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=message.from_user.id).set_state(States.THROTTLER)
    *_, user = user_data
    login = message.text.lower().strip()
    keyboard = None
    peer, text = await text_compile.peer_data_compile(user=user, login=login, is_single=True)
    if peer:
        friends = await UserPeer.get_friends(user_id=user.id)
        observables = await UserPeer.get_observables(user_id=user.id)
        keyboard = peer_keyboard(peers=[peer], friends=friends, observables=observables)
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    await message.answer(text, reply_markup=keyboard)


@dp.message_handler(state='granted')
async def peers_data(message: Message, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=message.from_user.id).set_state(States.THROTTLER)
    *_, user = user_data
    peer_logins, bad_logins = await text_compile.logins_separation(message_text=message.text)
    message = await message.answer(Config.local.wait.get(user.language))
    texts = []
    peers = []
    for login in peer_logins:
        await message.bot.send_chat_action(user.id, 'typing')
        peer, text = await text_compile.peer_data_compile(user=user, login=login, is_single=False)
        if peer:
            peers.append(peer)
        texts.append(text)
        with suppress(MessageNotModified, MessageToEditNotFound):
            await message.edit_text('\n\n'.join(texts))
    for login in bad_logins:
        text = Config.local.not_found.get(user.language, login=login.replace("<", "&lt"))
        texts.append(text)
    friends = await UserPeer.get_friends(user_id=user.id)
    observables = await UserPeer.get_observables(user_id=user.id)
    keyboard = peer_keyboard(peers=peers, friends=friends, observables=observables)
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    with suppress(MessageToDeleteNotFound, MessageCantBeDeleted):
        await message.delete()
    await message.answer('\n\n'.join(texts), reply_markup=keyboard)
