from contextlib import suppress
from typing import (Callable,
                    Tuple)

from aiogram.types import (CallbackQuery,
                           InlineKeyboardMarkup)
from aiogram.utils.exceptions import (MessageCantBeDeleted,
                                      MessageNotModified,
                                      MessageToEditNotFound,
                                      MessageToDeleteNotFound)
from aiogram.utils.parts import paginate
from asyncpg.exceptions import UniqueViolationError

from bot import dp
from config import Config
from db_models.campuses import Campus
from db_models.peers import Peer
from db_models.projects import Project
from db_models.users import User
from db_models.users_peers import UserPeer
from services.keyboards import (alone_peer_keyboard,
                                courses_keyboard,
                                data_keyboard,
                                keyboard_normalize,
                                pagination_keyboard,
                                peer_keyboard)
from services.states import States
from utils.text_compile import text_compile
from .messages_handlers import get_text_and_keyboard


async def action_peer(user: User, callback_query: CallbackQuery, method: Callable, action: str = None, limit: int = 3,
                      stop: int = 0) -> Tuple[str, InlineKeyboardMarkup]:
    await dp.current_state(user=user.id).set_state(States.THROTTLER)
    login = callback_query.data.split('.')[-1]
    message = await callback_query.message.edit_text(Config.local.wait.get(user.language))
    await message.bot.send_chat_action(user.id, 'typing')
    return await get_text_and_keyboard(user=user, message=message, method=method, login=login, action=action,
                                       limit=limit, stop=stop)


async def action_peers(user: User, callback_query: CallbackQuery, current_count: int, trigger: str,
                       alert_text: str, method: Callable, text: Callable):
    switch, peer_id, login, payload = callback_query.data.split('.')
    if current_count == 30 and switch == trigger:
        await callback_query.answer(alert_text, show_alert=True)
    else:
        await callback_query.answer(text(user.language, login=login), show_alert=True)
        with suppress(UniqueViolationError):
            await method(user_id=user.id, peer_id=int(peer_id))
        friends = await UserPeer.get_friends(user_id=user.id)
        observables = await UserPeer.get_observables(user_id=user.id)
        keyboard = keyboard_normalize(buttons=callback_query.message.reply_markup.inline_keyboard,
                                      friends=friends, observables=observables, payload=payload)
        with suppress(MessageNotModified, MessageToEditNotFound):
            await callback_query.message.edit_reply_markup(reply_markup=keyboard)
    await dp.current_state(user=user.id).set_state(States.GRANTED)


@dp.callback_query_handler(text_startswith='courses_campuses', state='granted')
async def campus_projects(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=callback_query.from_user.id).set_state(States.THROTTLER)
    *_, user = user_data
    cursus_id, campus_id = map(int, callback_query.data.split('.')[1:-1])
    projects = await Project.get_projects(cursus_id=cursus_id)
    keyboard = data_keyboard(data=projects, action='projects',  content=f'{cursus_id}={campus_id}', limit=30,
                             back_button_data=(Config.local.back.get(user.language), f'back.courses.{cursus_id}'))
    text = Config.local.project_choose.get(user.language)
    await callback_query.answer()
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    with suppress(MessageNotModified, MessageToEditNotFound):
        await callback_query.message.edit_text(text, reply_markup=keyboard)


@dp.callback_query_handler(text_startswith='courses', state='granted')
async def courses(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=callback_query.from_user.id).set_state(States.THROTTLER)
    campus, _, user = user_data
    cursus_id = int(callback_query.data.split('.')[1])
    back_button_data = (Config.local.back.get(user.language), 'back.courses')
    if user.use_default_campus:
        projects = await Project.get_projects(cursus_id=cursus_id)
        keyboard = data_keyboard(data=projects, action='projects', content=f'{cursus_id}={campus.id}',
                                 limit=30, back_button_data=back_button_data)
        text = Config.local.project_choose.get(user.language)
    else:
        campuses = await Campus.get_campuses()
        keyboard = data_keyboard(data=campuses, action='courses_campuses', content=cursus_id,
                                 limit=30, back_button_data=back_button_data)
        text = Config.local.campus_choose.get(user.language)
    await callback_query.answer()
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    with suppress(MessageNotModified, MessageToEditNotFound):
        await callback_query.message.edit_text(text, reply_markup=keyboard)


@dp.callback_query_handler(is_back_to_courses=True, state='granted')
async def back_to_courses(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=callback_query.from_user.id).set_state(States.THROTTLER)
    *_, user = user_data
    await callback_query.answer()
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    with suppress(MessageNotModified, MessageToEditNotFound):
        await callback_query.message.edit_text(Config.local.cursus_choose.get(user.language),
                                               reply_markup=courses_keyboard())


@dp.callback_query_handler(is_back_to_campuses_from_courses=True, state='granted')
async def back_to_campuses_from_courses(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    query = callback_query.data
    callback_query.data = query[query.index('.') + 1:]
    await courses(callback_query=callback_query, user_data=user_data)


@dp.callback_query_handler(text_startswith='locations_campuses', state='granted')
async def campus_projects(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=callback_query.from_user.id).set_state(States.THROTTLER)
    *_, user = user_data
    campus_id = int(callback_query.data.split('.')[2])
    with suppress(MessageToDeleteNotFound, MessageCantBeDeleted):
        await callback_query.message.delete()
    message = await callback_query.message.answer(Config.local.wait.get(user.language))
    await callback_query.message.bot.send_chat_action(user.id, 'typing')
    text, count, _ = await text_compile.free_locations_compile(user=user, campus_id=campus_id)
    back_button_data = (Config.local.back.get(user.language), 'back.locations')
    keyboard = pagination_keyboard(action='locations_pagination', count=count, content=campus_id,
                                   limit=40, stop=9, back_button_data=back_button_data)
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    with suppress(MessageToDeleteNotFound, MessageCantBeDeleted):
        await message.delete()
    await message.answer(text, reply_markup=keyboard)


@dp.callback_query_handler(is_back_to_campuses_from_locations=True, state='granted')
async def back_to_campuses_from_locations(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=callback_query.from_user.id).set_state(States.THROTTLER)
    *_, user = user_data
    campuses = await Campus.get_campuses()
    keyboard = data_keyboard(data=campuses, action='locations_campuses', content='locations', limit=30)
    await callback_query.answer()
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    with suppress(MessageNotModified, MessageToEditNotFound):
        await callback_query.message.edit_text(Config.local.campus_choose.get(user.language), reply_markup=keyboard)


@dp.callback_query_handler(text_startswith='campuses', state='granted')
async def campus_locations(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=callback_query.from_user.id).set_state(States.THROTTLER)
    *_, user = user_data
    campus_id = int(callback_query.data.split('.')[2])
    message = await callback_query.message.edit_text(Config.local.wait.get(user.language))
    text, count, _ = await text_compile.free_locations_compile(user=user, campus_id=campus_id)
    keyboard = pagination_keyboard(action='locations_pagination', count=count, content=campus_id, limit=40, stop=9)
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    with suppress(MessageToDeleteNotFound, MessageCantBeDeleted):
        await message.delete()
    await message.answer(text, reply_markup=keyboard)


@dp.callback_query_handler(text_startswith=('on', 'off'), state='granted')
async def observations_actions(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=callback_query.from_user.id).set_state(States.THROTTLER)
    *_, user = user_data
    observed_count = await UserPeer.get_observed_count(user_id=user.id)
    alert_text = Config.local.observed_count.get(user.language)
    variants = {'on': (UserPeer.add_observable, Config.local.observation_on.get),
                'off': (UserPeer.remove_observable, Config.local.observation_off.get)}
    method, text = variants[callback_query.data.split('.')[0]]
    await action_peers(user=user, callback_query=callback_query, current_count=observed_count, trigger='on',
                       alert_text=alert_text, method=method, text=text)


@dp.callback_query_handler(is_remove_friend=True, state='granted')
async def friends_list(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=callback_query.from_user.id).set_state(States.THROTTLER)
    *_, user = user_data
    peer_id, login = callback_query.data.split('.')[1:-1]
    alert_text = Config.local.remove_friend.get(user.language, login=login)
    await callback_query.answer(alert_text, show_alert=True)
    await UserPeer.remove_friend(user_id=user.id, peer_id=int(peer_id))
    friends_count = await UserPeer.get_friends_count(user_id=user.id)
    friends = await UserPeer.get_friends(user_id=user.id)
    observables = await UserPeer.get_observables(user_id=user.id)
    current_page = 1
    raws = [button.callback_data for row in callback_query.message.reply_markup.inline_keyboard
            for button in row][-1].split('.')
    if friends_count + 1 > 10 and raws[0] == 'friends_pagination':
        current_page = int(raws[1])
    text, page = await text_compile.friends_list_normalization(user=user, current_page=current_page, removable=login,
                                                               friends=friends, friends_count=friends_count)
    count = len(friends[(page - 1) * 10:])
    friends = paginate(friends, page=page - 1, limit=10)
    payload = ''
    if friends_count > 11:
        payload = 'pagination'
    if friends_count == 1:
        payload = 'alone_peer'
    keyboard = peer_keyboard(peers=friends, friends=friends, observables=observables, payload=payload)
    if friends_count + 1 > 10:
        keyboard = pagination_keyboard(action='friends_pagination', count=count, content=current_page,
                                       limit=10, stop=3, page=page - 1, keyboard=keyboard)
    if friends_count == 1:
        keyboard = alone_peer_keyboard(user=user, login=friends[0].login, keyboard=keyboard)
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    with suppress(MessageNotModified, MessageToEditNotFound):
        await callback_query.message.edit_text(text, reply_markup=keyboard,
                                               disable_web_page_preview=not (friends_count == 1 and user.show_avatar))


@dp.callback_query_handler(text_startswith=('add', 'remove'), state='granted')
async def friends_actions(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=callback_query.from_user.id).set_state(States.THROTTLER)
    *_, user = user_data
    friends_count = await UserPeer.get_friends_count(user_id=user.id)
    alert_text = Config.local.friends_count.get(user.language)
    variants = {'add': (UserPeer.add_friend, Config.local.add_friend.get),
                'remove': (UserPeer.remove_friend, Config.local.remove_friend.get)}
    method, text = variants[callback_query.data.split('.')[0]]
    await action_peers(user=user, callback_query=callback_query, current_count=friends_count,
                       trigger='add', alert_text=alert_text, method=method, text=text)


@dp.callback_query_handler(text_startswith='projects', state='granted')
async def projects_(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=callback_query.from_user.id).set_state(States.THROTTLER)
    *_, user = user_data
    content, project_id, page = callback_query.data.split('.')[1:]
    project_id = int(project_id)
    cursus_id, campus_id = map(int, content.split('='))
    await callback_query.message.bot.send_chat_action(user.id, 'typing')
    text = await text_compile.project_peers_compile(user=user, project_id=project_id, campus_id=campus_id)
    projects = await Project.get_projects(cursus_id=cursus_id)
    back_button_data = (Config.local.back.get(user.language), 'back.courses')
    if not user.use_default_campus:
        back_button_data = (Config.local.back.get(user.language), f'back.courses.{cursus_id}')
    keyboard = data_keyboard(data=projects, action='projects', content=content, limit=30, current_id=project_id,
                             page=int(page), back_button_data=back_button_data)
    await callback_query.answer()
    with suppress(MessageToDeleteNotFound, MessageCantBeDeleted):
        await callback_query.message.delete()
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    await callback_query.message.answer(text, reply_markup=keyboard)


@dp.callback_query_handler(text_startswith='back.peer', state='granted')
async def back_to_peer(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    *_, user = user_data
    await dp.current_state(user=user.id).set_state(States.THROTTLER)
    login = callback_query.data.split('.')[-1]
    message = await callback_query.message.edit_text(Config.local.wait.get(user.language))
    await message.bot.send_chat_action(user.id, 'typing')
    peer, text = await text_compile.peer_data_compile(user=user, login=login, is_single=True)
    friends = await UserPeer.get_friends(user_id=user.id)
    observables = await UserPeer.get_observables(user_id=user.id)
    keyboard = peer_keyboard(peers=[peer], friends=friends, observables=observables, payload='alone_peer')
    keyboard = alone_peer_keyboard(user=user, login=peer.login, keyboard=keyboard)
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    with suppress(MessageToDeleteNotFound, MessageCantBeDeleted):
        await message.delete()
    await callback_query.message.answer(text, reply_markup=keyboard, disable_web_page_preview=not user.show_avatar)


@dp.callback_query_handler(text_startswith='last_locations', state='granted')
async def peer_locations(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    text, keyboard = await action_peer(user=user_data[-1], callback_query=callback_query,
                                       method=text_compile.peer_locations_compile,
                                       action='peer_locations_pagination', limit=10, stop=4)
    await callback_query.message.answer(text, reply_markup=keyboard)


@dp.callback_query_handler(text_startswith='time_statistics', state='granted')
async def peer_times(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    text, keyboard = await action_peer(user=user_data[-1], callback_query=callback_query,
                                       method=text_compile.time_peers_compile)
    await callback_query.message.answer(text, reply_markup=keyboard)


@dp.callback_query_handler(text_startswith='feedbacks', state='granted')
async def peer_feedbacks(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    text, keyboard = await action_peer(user=user_data[-1], callback_query=callback_query,
                                       method=text_compile.peer_feedbacks_compile,
                                       action='feedbacks_pagination', limit=5, stop=9)
    await callback_query.message.answer(text, disable_web_page_preview=True, reply_markup=keyboard)
