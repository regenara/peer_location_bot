import asyncio

from aiogram.types import Message
from aiogram.utils.exceptions import BotBlocked
from aiogram.utils.exceptions import ChatNotFound
from aiogram.utils.exceptions import UserDeactivated

from data.config import ADMIN
from misc import dp
from misc import mongo
from models.user import User
from services.keyboards import menu_keyboard


@dp.message_handler(state='mailing', content_types='any')
async def mailing(message: Message):
    await dp.current_state(user=ADMIN).finish()
    if message.text == '$':
        await message.answer('Отменено')
    else:
        await message.answer('Рассылка началась')
        cursor = await mongo.get_collections('users')
        collections = await cursor.to_list(length=100)
        while collections:
            for collection in collections:
                user = User.from_dict(collection)
                try:
                    await message.copy_to(user.user_id, reply_markup=menu_keyboard(user.lang))
                    await asyncio.sleep(0.25)
                except (BotBlocked, UserDeactivated):
                    await mongo.delete('users', {'user_id': user.user_id})
                except ChatNotFound:
                    pass
            collections = await cursor.to_list(length=100)
        await message.answer('Готово!')


@dp.message_handler(is_mailing=True)
async def before_mailing(message: Message):
    await message.answer("Пришли сообщение, которое надо разослать, или отправь $ для отмены")
