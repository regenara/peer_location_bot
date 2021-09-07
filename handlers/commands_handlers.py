from contextlib import suppress
from typing import Tuple

from aiogram.types import Message
from aiogram.utils.exceptions import (BadRequest,
                                      MessageCantBeDeleted,
                                      MessageToDeleteNotFound,
                                      MessageToEditNotFound)
from aiogram.utils.markdown import hbold

from bot import dp
from config import Config
from db_models.campuses import Campus
from db_models.peers import Peer
from db_models.users import User
from db_models.users_peers import UserPeer
from services.keyboards import (auth_keyboard,
                                courses_keyboard,
                                data_keyboard,
                                donate_keyboard,
                                menu_keyboard,
                                pagination_keyboard,
                                peer_keyboard,
                                settings_keyboard)
from services.states import States
from utils.text_compile import text_compile


@dp.message_handler(is_unauthorized=True, state='*')
async def welcome(message: Message):
    await dp.current_state(user=message.from_user.id).set_state(States.AUTH)
    language_code = message.from_user.language_code if message.from_user.language_code in ('ru', 'en') else 'en'
    user_id = message.from_user.id
    message = await message.answer('🗿')
    await message.edit_text(Config.local.need_auth.get(language_code),
                            reply_markup=auth_keyboard(message_id=message.message_id, user_id=user_id,
                                                       language_code=language_code))


@dp.message_handler(lambda message: message.text in ('/start', Config.local.settings.ru, Config.local.settings.en),
                    state='*')
async def settings(message: Message, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=message.from_user.id).set_state(States.GRANTED)
    _, peer, user = user_data
    if message.text == '/start':
        await message.answer(Config.local.hello.get(user.language, login=peer.login),
                             reply_markup=menu_keyboard(user.language))
    await message.answer(Config.local.help_text.get(user.language), reply_markup=settings_keyboard(user=user))


@dp.message_handler(is_introvert=True, state='granted')
async def friend_data(message: Message, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=message.from_user.id).set_state(States.THROTTLER)
    *_, user = user_data
    keyboard = None
    friends = await UserPeer.get_friends(user_id=user.id)
    if not friends:
        text = Config.local.no_friends.get(user.language)
    else:
        observables = await UserPeer.get_observables(user_id=user.id)
        peer, text = await text_compile.peer_data_compile(user=user, login=friends[0].login, is_single=True)
        keyboard = peer_keyboard(peers=[peer], friends=friends, observables=observables)
        text = f'{hbold(Config.local.friends_list.get(user.language))}\n\n{text}'
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    await message.answer(text, reply_markup=keyboard)


@dp.message_handler(lambda message: message.text in ('/friends', Config.local.friends.ru, Config.local.friends.en),
                    state='granted')
async def friends_data(message: Message, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=message.from_user.id).set_state(States.THROTTLER)
    *_, user = user_data
    title = Config.local.friends_list.get(user.language)
    message = await message.answer(Config.local.wait.get(user.language))
    texts = ['']
    friends = await UserPeer.get_friends(user_id=user.id)
    friends_count = await UserPeer.get_friends_count(user_id=user.id)
    observables = await UserPeer.get_observables(user_id=user.id)
    for i, friend in enumerate(friends, 1):
        texts[0] = f'{title} ({i}/{friends_count})'
        peer, text = await text_compile.peer_data_compile(user=user, login=friend.login, is_single=False)
        texts.append(text)
        try:
            await message.edit_text('\n\n'.join(texts))
        except BadRequest:
            texts.pop(-1)
            break
        except MessageToEditNotFound:
            pass
    texts[0] = title
    text = '\n\n'.join(texts)
    keyboard = peer_keyboard(peers=friends, friends=friends, observables=observables)
    with suppress(MessageToDeleteNotFound, MessageCantBeDeleted):
        await message.delete()
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    await message.answer(text, reply_markup=keyboard)


@dp.message_handler(lambda message: message.text in ('/projects', Config.local.projects.ru, Config.local.projects.en),
                    state='*')
async def projects(message: Message, user_data: Tuple[Campus, Peer, User]):
    *_, user = user_data
    await message.answer(Config.local.cursus_choose.get(user.language), reply_markup=courses_keyboard())


@dp.message_handler(lambda message: message.text in ('/locations', Config.local.locations.ru,
                                                     Config.local.locations.en), state='granted')
async def free_locations(message: Message, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=message.from_user.id).set_state(States.THROTTLER)
    _, peer, user = user_data
    if user.use_default_campus:
        message = await message.answer(Config.local.wait.get(user.language))
        text, count, _ = await text_compile.free_locations_compile(user=user, campus_id=peer.campus_id)
        keyboard = pagination_keyboard(action='locations_pagination', count=count,
                                       content=peer.campus_id, limit=40, stop=9)
        with suppress(MessageToDeleteNotFound, MessageCantBeDeleted):
            await message.delete()
        await message.answer(text, reply_markup=keyboard)
    else:
        campuses = await Campus.get_campuses()
        keyboard = data_keyboard(data=campuses, action='locations_campuses', content='locations', limit=30)
        await message.answer(Config.local.campus_choose.get(user.language), reply_markup=keyboard)
    await dp.current_state(user=user.id).set_state(States.GRANTED)


@dp.message_handler(lambda message: message.text in ('/about', Config.local.about.ru, Config.local.about.en),
                    state='*')
async def about(message: Message):
    await message.answer('<a href="https://github.com/JakeBV/peer_location_bot">Source</a>')


@dp.message_handler(lambda message: message.text in ('/donate', Config.local.donate.ru, Config.local.donate.en),
                    state='*')
async def donate(message: Message, user_data: Tuple[Campus, Peer, User]):
    *_, user = user_data
    text = await text_compile.donate_text_compile(user=user)
    await message.answer(text, reply_markup=donate_keyboard(user.language))
