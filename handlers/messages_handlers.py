from contextlib import suppress
from typing import (Callable,
                    Tuple)

from aiogram.types import (InlineKeyboardMarkup,
                           Message)
from aiogram.utils.exceptions import (MessageCantBeDeleted,
                                      MessageToDeleteNotFound,
                                      MessageNotModified,
                                      MessageToEditNotFound)

from bot import (bot,
                 dp)
from config import Config
from db_models.campuses import Campus
from db_models.peers import Peer
from db_models.users import User
from db_models.users_peers import UserPeer
from services.keyboards import (alone_peer_keyboard,
                                pagination_keyboard,
                                peer_keyboard)
from services.states import States
from utils.text_compile import text_compile


async def get_text_and_keyboard(user: User, message: Message, method: Callable, login: str,
                                action: str, limit: int, stop: int) -> Tuple[str, InlineKeyboardMarkup]:
    data = await method(user=user, login=login)
    back_button_data = (Config.local.back.get(user.language), f'back.peer.{login}')
    if len(data) == 2:
        text, is_peer = data
        count = 1
    else:
        text, count, is_peer = data
    keyboard = None
    if is_peer:
        keyboard = pagination_keyboard(action=action, count=count, content=login, limit=limit, stop=stop,
                                       back_button_data=back_button_data)
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    with suppress(MessageToDeleteNotFound, MessageCantBeDeleted):
        await message.delete()
    return text, keyboard


async def action_peer(user: User, message: Message, method: Callable, action: str = None, limit: int = 3,
                      stop: int = 0) -> Tuple[str, InlineKeyboardMarkup]:
    await dp.current_state(user=user.id).set_state(States.THROTTLER)
    login = message.text[1:].lower().strip()
    message = await message.answer(Config.local.wait.get(user.language))
    await message.bot.send_chat_action(user.id, 'typing')
    return await get_text_and_keyboard(user=user, message=message, method=method, login=login, action=action,
                                       limit=limit, stop=stop)


@dp.message_handler(lambda message: message.text.startswith('@') and len(message.text) > 2, state='granted')
async def peer_data_from_username(message: Message, user_data: Tuple[Campus, Peer, User]):
    *_, user = user_data
    username_or_user_id = message.text[1:].lower().strip()
    login = await User.get_login(username_or_user_id=username_or_user_id)
    if not login:
        await message.answer(Config.local.not_found_username.get(user.language,
                                                                 username=username_or_user_id.replace("<", "&lt")))
    else:
        message.text = login
        await peer_data(message=message, user_data=user_data)


@dp.message_handler(lambda message: message.text.startswith('?') and len(message.text) > 2, state='granted')
async def peer_locations(message: Message, user_data: Tuple[Campus, Peer, User]):
    text, keyboard = await action_peer(user=user_data[-1], message=message, method=text_compile.peer_locations_compile,
                                       action='peer_locations_pagination', limit=10, stop=4)
    await message.answer(text, reply_markup=keyboard)


@dp.message_handler(lambda message: message.text.startswith('&') and len(message.text) > 2, state='granted')
async def peer_times(message: Message, user_data: Tuple[Campus, Peer, User]):
    text, keyboard = await action_peer(user=user_data[-1], message=message, method=text_compile.time_peers_compile)
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
        keyboard = peer_keyboard(peers=[peer], friends=friends, observables=observables, payload='pagination')
        keyboard = pagination_keyboard(action='host_pagination', count=1, content=host, limit=0,
                                       stop=3, keyboard=keyboard)
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    with suppress(MessageToDeleteNotFound, MessageCantBeDeleted):
        await message.delete()
    await bot.send_message(user.id, text, reply_markup=keyboard, disable_web_page_preview=not user.show_avatar)


@dp.message_handler(lambda message: len(message.text.split()) == 1, state='granted')
async def peer_data(message: Message, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=message.from_user.id).set_state(States.THROTTLER)
    *_, user = user_data
    await message.bot.send_chat_action(user.id, 'typing')
    login = message.text.lower().strip()
    keyboard = None
    peer, text = await text_compile.peer_data_compile(user=user, login=login, is_single=True)
    if peer:
        friends = await UserPeer.get_friends(user_id=user.id)
        observables = await UserPeer.get_observables(user_id=user.id)
        keyboard = peer_keyboard(peers=[peer], friends=friends, observables=observables, payload='alone_peer')
        keyboard = alone_peer_keyboard(user=user, login=peer.login, keyboard=keyboard)
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    await message.answer(text, reply_markup=keyboard, disable_web_page_preview=not user.show_avatar)


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
            await message.edit_text('\n\n'.join(texts), disable_web_page_preview=True)
    for login in bad_logins:
        text = Config.local.not_found.get(user.language, login=login.replace("<", "&lt"))
        texts.append(text)
    friends = await UserPeer.get_friends(user_id=user.id)
    observables = await UserPeer.get_observables(user_id=user.id)
    if len(peers) == 1:
        keyboard = peer_keyboard(peers=peers, friends=friends, observables=observables, payload='alone_peer')
        keyboard = alone_peer_keyboard(user=user, login=peers[0].login, keyboard=keyboard)
    else:
        keyboard = peer_keyboard(peers=peers, friends=friends, observables=observables)
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    with suppress(MessageToDeleteNotFound, MessageCantBeDeleted):
        await message.delete()
    await bot.send_message(user.id, '\n\n'.join(texts), reply_markup=keyboard,
                           disable_web_page_preview=user.show_avatar and len(peers) != 1)
