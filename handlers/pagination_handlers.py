from contextlib import suppress
from typing import Tuple

from aiogram.types import CallbackQuery
from aiogram.utils.exceptions import MessageNotModified

from bot import dp
from config import Config
from db_models.campuses import Campus
from db_models.peers import Peer
from db_models.projects import Project
from db_models.users import User
from db_models.users_peers import UserPeer
from services.keyboards import (data_keyboard,
                                pagination_keyboard,
                                peer_keyboard)
from services.states import States
from utils.text_compile import text_compile


@dp.callback_query_handler(text_startswith='projects_pagination', state='granted')
async def projects_pagination(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=callback_query.from_user.id).set_state(States.THROTTLER)
    campus, _, user = user_data
    content, page = callback_query.data.split('.')[1:]
    cursus_id = int(content.split('=')[0])
    projects = await Project.get_projects(cursus_id=cursus_id)
    back_button_data = (Config.local.back.get(user.language), 'back.courses')
    if not user.use_default_campus:
        back_button_data = (Config.local.back.get(user.language), f'back.courses.{cursus_id}')
    keyboard = data_keyboard(data=projects, action='projects', content=content, limit=30, page=int(page),
                             back_button_data=back_button_data)
    await callback_query.answer()
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    with suppress(MessageNotModified):
        await callback_query.message.edit_text(Config.local.project_choose.get(user.language), reply_markup=keyboard)


@dp.callback_query_handler(text_startswith='locations_pagination', state='granted')
async def free_locations_pagination(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=callback_query.from_user.id).set_state(States.THROTTLER)
    *_, user = user_data
    campus_id, page = map(int, callback_query.data.split('.')[1:])
    text, count, page = await text_compile.free_locations_compile(user=user, campus_id=campus_id, page=page)
    back_button_data = None
    if not user.use_default_campus:
        back_button_data = (Config.local.back.get(user.language), 'back.locations')
    keyboard = pagination_keyboard(action='locations_pagination', count=count, content=campus_id, limit=40,
                                   stop=9, page=page, back_button_data=back_button_data)
    await callback_query.answer()
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    with suppress(MessageNotModified):
        await callback_query.message.edit_text(text, reply_markup=keyboard)


@dp.callback_query_handler(text_startswith='peer_locations_pagination', state='granted')
async def peer_locations_pagination(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=callback_query.from_user.id).set_state(States.THROTTLER)
    *_, user = user_data
    login, page = callback_query.data.split('.')[1:]
    page = int(page)
    text, count = await text_compile.peer_locations_compile(user=user, login=login, page=page,
                                                            message_text=callback_query.message.text)
    keyboard = pagination_keyboard(action='peer_locations_pagination', count=count, content=login,
                                   limit=10, stop=4, page=page)
    await callback_query.answer()
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    with suppress(MessageNotModified):
        await callback_query.message.edit_text(text, disable_web_page_preview=True, reply_markup=keyboard)


@dp.callback_query_handler(text_startswith='feedbacks_pagination', state='granted')
async def feedbacks_pagination(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=callback_query.from_user.id).set_state(States.THROTTLER)
    *_, user = user_data
    login, page = callback_query.data.split('.')[1:]
    page = int(page)
    text, count = await text_compile.peer_feedbacks_compile(user=user, login=login, page=page,
                                                            message_text=callback_query.message.text)
    keyboard = pagination_keyboard(action='feedbacks_pagination', count=count, content=login,
                                   limit=5, stop=9, page=page)
    await callback_query.answer()
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    with suppress(MessageNotModified):
        await callback_query.message.edit_text(text, disable_web_page_preview=True, reply_markup=keyboard)


@dp.callback_query_handler(text_startswith='host_pagination', state='granted')
async def host_pagination(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=callback_query.from_user.id).set_state(States.THROTTLER)
    *_, user = user_data
    host, page = callback_query.data.split('.')[1:]
    page = int(page)
    text, peer = await text_compile.host_data_compile(user=user, host=host, page=page)
    keyboard = None
    if peer:
        friends = await UserPeer.get_friends(user_id=user.id)
        observables = await UserPeer.get_observables(user_id=user.id)
        keyboard = peer_keyboard(peers=[peer], friends=friends, observables=observables, payload='host')
    keyboard = pagination_keyboard(action='host_pagination', count=1, content=host, limit=0,
                                   stop=3, page=page, keyboard=keyboard)
    await callback_query.answer()
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    with suppress(MessageNotModified):
        await callback_query.message.edit_text(text, reply_markup=keyboard)


@dp.callback_query_handler(text_startswith=('courses_campuses_pagination', 'locations_campuses_pagination'),
                           state='granted')
async def campuses_pagination(callback_query: CallbackQuery, user_data: Tuple[Campus, Peer, User]):
    await dp.current_state(user=callback_query.from_user.id).set_state(States.THROTTLER)
    *_, user = user_data
    action = callback_query.data[:callback_query.data.rindex('_')]
    back_button_data = None
    if action == 'courses_campuses':
        back_button_data = (Config.local.back.get(user.language), 'back.courses')
    content, page = callback_query.data.split('.')[1:]
    campuses = await Campus.get_campuses()
    keyboard = data_keyboard(data=campuses, action=action, content=content, limit=30, page=int(page),
                             back_button_data=back_button_data)
    await callback_query.answer()
    await dp.current_state(user=user.id).set_state(States.GRANTED)
    with suppress(MessageNotModified):
        await callback_query.message.edit_reply_markup(reply_markup=keyboard)
