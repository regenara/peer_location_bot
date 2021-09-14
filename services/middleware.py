from aiogram.types import (CallbackQuery,
                           Message,
                           User)
from aiogram.dispatcher.middlewares import BaseMiddleware


class Middleware(BaseMiddleware):
    async def setup_chat(self, data: dict, user: User):
        from db_models.users import User as UserDB

        user_data = await UserDB.get_user_data(user_id=user.id)
        if user_data:
            if user.username != user_data[-1].username:
                await UserDB.update_user(user_id=user.id, username=user.username)

        data['user_data'] = user_data

    async def on_pre_process_message(self, message: Message, data: dict):
        await self.setup_chat(data, message.from_user)

    async def on_pre_process_callback_query(self, query: CallbackQuery, data: dict):
        await self.setup_chat(data, query.from_user)
