from aiogram.types import Message

from data.config import LOCALIZATION_TEXTS
from misc import dp
from misc import mongo
from models.user import User
from services.keyboards import auth_keyboard
from services.keyboards import language_keyboard
from services.states import States


@dp.message_handler(is_start=True, state='*')
async def send_welcome(message: Message, user: User):
    user_id = message.from_user.id
    await dp.current_state(user=user_id).finish()
    if not user:
        message = await message.answer('🗿')
        await dp.current_state(user=user_id).set_state(States.AUTH)
        await message.edit_text('Authorization required\nНеобходима авторизация',
                                reply_markup=auth_keyboard(message.message_id, user_id))
    else:
        text = LOCALIZATION_TEXTS['language'][user.lang].format(nickname=user.nickname)
        await message.answer(text, reply_markup=language_keyboard())


@dp.message_handler(is_help=True, state='*')
async def send_help(message: Message):
    user_id = message.from_user.id
    data = await mongo.find('users', {'user_id': user_id})
    user = User.from_dict(data)
    text = LOCALIZATION_TEXTS['help'][user.lang]
    await message.answer(text)


@dp.message_handler(is_about=True, state='*')
async def about(message: Message):
    await message.answer('<a href="https://github.com/JakeBV/peer_location_bot">Source</a>')


@dp.message_handler(is_donate=True, state='*')
async def donate(message: Message):
    await message.answer('<a href="https://donate.stream/jakebv">Donate for coffee</a>')
