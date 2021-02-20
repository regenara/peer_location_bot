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
from services.keyboards import projects_keyboard
from utils.text_compile import free_locations_compile
from utils.text_compile import peer_data_compile


@dp.message_handler(is_introvert=True)
@dp.throttled(throttled, rate=3)
async def friend_data(message: Message, user: User):
    peer_data_locale = LOCALIZATION_TEXTS['user_info'][user.lang]
    keyboard = None
    if not user.friends:
        peer_text = LOCALIZATION_TEXTS['friends'][user.lang]['no_friends']
    else:
        title = LOCALIZATION_TEXTS['friends'][user.lang]['list']
        peer_data = await peer_data_compile(user.friends[0], peer_data_locale, True)
        keyboard = peer_keyboard(user.friends, user.friends, user.notifications)
        peer_text = f'<b>{title}</b>\n\n{peer_data["text"]}'
    await message.answer(peer_text, reply_markup=keyboard)


@dp.message_handler(is_extrovert=True)
@dp.throttled(throttled, rate=20)
async def friends_data(message: Message):
    user_id = message.from_user.id
    data = await mongo.find('users', {'user_id': user_id})
    user = User.from_dict(data)
    title = LOCALIZATION_TEXTS['friends'][user.lang]['list']
    peer_data_locale = LOCALIZATION_TEXTS['user_info'][user.lang]
    text = LOCALIZATION_TEXTS['wait'][user.lang]
    message = await message.answer(text)
    texts = ['']
    for i, friend in enumerate(user.friends, 1):
        texts[0] = f'{title} ({i}/{user.friends_count})'
        peer_data = await peer_data_compile(friend, peer_data_locale, False)
        texts.append(peer_data['text'])
        text = '\n\n'.join(texts)
        with suppress(MessageToEditNotFound):
            await message.edit_text(text)
    with suppress(MessageToDeleteNotFound):
        await message.delete()
    texts[0] = title
    text = '\n\n'.join(texts)
    await message.answer(text, reply_markup=peer_keyboard(user.friends, user.friends, user.notifications))


@dp.message_handler(is_projects=True)
@dp.throttled(throttled, rate=5)
async def projects(message: Message):
    user_id = message.from_user.id
    data = await mongo.find('users', {'user_id': user_id})
    user = User.from_dict(data)
    keyboard = await projects_keyboard(0, 26)
    await message.answer(LOCALIZATION_TEXTS['projects'][user.lang]['choose'], reply_markup=keyboard)


@dp.message_handler(is_locations=True)
@dp.throttled(throttled, rate=15)
async def free_locations(message: Message):
    user_id = message.from_user.id
    data = await mongo.find('users', {'user_id': user_id})
    user = User.from_dict(data)
    free_locations_locale = LOCALIZATION_TEXTS['free_locations'][user.lang]
    message = await message.answer(LOCALIZATION_TEXTS['wait'][user.lang])
    free_locations_data = await free_locations_compile(user.campus_id, free_locations_locale)
    if free_locations_data.get('error'):
        locations_text = free_locations_data['error']
    else:
        locations_text = free_locations_data['text']
    count = free_locations_data['count']
    with suppress(MessageToDeleteNotFound):
        await message.delete()
    scan_time = free_locations_data['scan_time']
    await message.answer(locations_text,
                         reply_markup=pagination_keyboard('free_locations', count, scan_time, 40, 9))
