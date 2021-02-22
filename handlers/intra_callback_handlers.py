from contextlib import suppress

from aiogram.types import CallbackQuery
from aiogram.utils.exceptions import MessageNotModified
from aiogram.utils.exceptions import MessageToDeleteNotFound

from data.config import LOCALIZATION_TEXTS
from misc import dp
from misc import mongo
from models.user import User
from services.keyboards import pagination_keyboard
from services.keyboards import peer_keyboard
from services.keyboards import projects_keyboard
from services.states import States
from utils.text_compile import free_locations_compile
from utils.text_compile import host_data_compile
from utils.text_compile import peer_feedbacks_compile
from utils.text_compile import peer_locations_compile
from utils.text_compile import project_peers_compile


@dp.callback_query_handler(lambda callback: callback.data.split('=')[-1] == 'pagination')
async def projects_pagination(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    page = callback_query.data.split('=')[2]
    data = await mongo.find('users', {'user_id': user_id})
    user = User.from_dict(data)
    keyboard = await projects_keyboard(int(page), 26)
    await callback_query.answer()
    with suppress(MessageNotModified):
        await callback_query.message.edit_text(LOCALIZATION_TEXTS['projects'][user.lang]['choose'],
                                               reply_markup=keyboard)


@dp.callback_query_handler(lambda callback: callback.data.split('=')[0] == 'projects')
async def project(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await dp.current_state(user=user_id).set_state(States.THROTTLER)
    project_id, page = callback_query.data.split('=')[1:]
    project_id = int(project_id)
    data = await mongo.find('users', {'user_id': user_id})
    user = User.from_dict(data)
    projects_locale = LOCALIZATION_TEXTS['projects'][user.lang]
    await callback_query.answer(f'⏳ {LOCALIZATION_TEXTS["wait"][user.lang]}')
    project_data = await project_peers_compile(project_id, user.campus_id, user.campus, user.time_zone, projects_locale)
    await dp.current_state(user=user_id).finish()
    if project_data.get('error'):
        await callback_query.message.edit_text(project_data['error'])
    else:
        with suppress(MessageToDeleteNotFound):
            await callback_query.message.delete()
        keyboard = await projects_keyboard(int(page), 26, project_id)
        await callback_query.message.answer(project_data['text'], reply_markup=keyboard)


@dp.callback_query_handler(lambda callback: callback.data.split('=')[0] == 'host')
async def host_actions(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await dp.current_state(user=user_id).set_state(States.THROTTLER)
    host, page, campus = callback_query.data.split('=')[1:]
    page = int(page)
    data = await mongo.find('users', {'user_id': user_id})
    user = User.from_dict(data)
    host_data_locale = LOCALIZATION_TEXTS['host'][user.lang]
    peer_data_locale = LOCALIZATION_TEXTS['user_info'][user.lang]
    host_data = await host_data_compile(host, host_data_locale, peer_data_locale, user.avatar, page, campus)
    await callback_query.answer()
    peer_kb = None
    if not host_data.get('several'):
        peer_kb = peer_keyboard([host_data['peer']], user.friends, user.notifications)
    keyboard = pagination_keyboard('host', 1, host_data['host'], 0, 3, page, peer_kb, campus)
    await dp.current_state(user=user_id).finish()
    await callback_query.message.edit_text(host_data['text'], reply_markup=keyboard)


@dp.callback_query_handler(is_locations_renewal=True)
async def free_locations_renewal(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = await mongo.find('users', {'user_id': user_id})
    user = User.from_dict(data)
    await callback_query.answer(f'⏳ {LOCALIZATION_TEXTS["wait"][user.lang]}')
    free_locations_locale = LOCALIZATION_TEXTS['free_locations'][user.lang]
    free_locations_data = await free_locations_compile(user.campus_id, free_locations_locale)
    await dp.current_state(user=user_id).finish()
    if free_locations_data.get('error'):
        await callback_query.message.edit_text(free_locations_data['error'])
    else:
        locations_text = free_locations_data['text']
        scan_time = free_locations_data['scan_time']
        count = free_locations_data['count']
        page = free_locations_data['page']
        keyboard = pagination_keyboard('free_locations', count, scan_time, 40, 9, page)
        with suppress(MessageNotModified):
            await callback_query.message.edit_text(locations_text, reply_markup=keyboard)


@dp.callback_query_handler(lambda callback: callback.data.split('=')[0] == 'free_locations')
async def free_locations_actions(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    scan_time, page = callback_query.data.split('=')[1:]
    data = await mongo.find('users', {'user_id': user_id})
    user = User.from_dict(data)
    free_locations_locale = LOCALIZATION_TEXTS['free_locations'][user.lang]
    free_locations_data = await free_locations_compile(user.campus_id, free_locations_locale, int(page))
    await callback_query.answer()
    if free_locations_data.get('error'):
        await callback_query.message.edit_text(free_locations_data['error'])
    else:
        locations_text = free_locations_data['text']
        scan_time = free_locations_data['scan_time']
        count = free_locations_data['count']
        page = free_locations_data['page']
        keyboard = pagination_keyboard('free_locations', count, scan_time, 40, 9, page)
        with suppress(MessageNotModified):
            await callback_query.message.edit_text(locations_text, reply_markup=keyboard)


@dp.callback_query_handler(lambda callback: callback.data.split('=')[0] in ('locations', 'feedbacks'))
async def locations_and_feedbacks_actions(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    action, nickname, page = callback_query.data.split('=')
    message_text = callback_query.message.text
    page = int(page)
    data = await mongo.find('users', {'user_id': user_id})
    user = User.from_dict(data)
    if not page:
        await dp.current_state(user=user_id).set_state(States.THROTTLER)
        await callback_query.answer(f'⏳ {LOCALIZATION_TEXTS["wait"][user.lang]}')
    if action == 'locations':
        results = 10
        stop = 4
        peer_locations_locale = LOCALIZATION_TEXTS['last_locations'][user.lang]
        params = await peer_locations_compile(nickname, peer_locations_locale, page, message_text)
    else:
        results = 5
        stop = 9
        peer_feedbacks_locale = LOCALIZATION_TEXTS['feedbacks'][user.lang]
        params = await peer_feedbacks_compile(nickname, peer_feedbacks_locale, page, message_text)
    web_preview = stop == 9
    if page:
        await callback_query.answer()
    keyboard = pagination_keyboard(action, params['count'], nickname, results, stop, page)
    await dp.current_state(user=user_id).finish()
    await callback_query.message.edit_text(params['text'], disable_web_page_preview=web_preview, reply_markup=keyboard)
