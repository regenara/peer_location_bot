from aiogram.types import (CallbackQuery,
                           Message,
                           User)
from aiogram.dispatcher.middlewares import BaseMiddleware


class Middleware(BaseMiddleware):
    async def setup_chat(self, data: dict, user: User):
        from db_models.campuses import Campus
        from db_models.peers import Peer
        from db_models.users import User as UserDB

        user_data = await UserDB.get_user_data(user_id=user.id)
        if user_data:
            campus_obj, peer_obj, user_obj = user_data
            user_data = (Campus.from_dict(data=campus_obj) if isinstance(campus_obj, dict) else campus_obj,
                         Peer.from_dict(data=peer_obj) if isinstance(peer_obj, dict) else peer_obj,
                         UserDB.from_dict(data=user_obj) if isinstance(user_obj, dict) else user_obj)
            if user.username != user_data[-1].username:
                await UserDB.update_user(user_id=user.id, username=user.username)

        data['user_data'] = user_data

    async def on_pre_process_message(self, message: Message, data: dict):
        await self.setup_chat(data, message.from_user)

    async def on_pre_process_callback_query(self, query: CallbackQuery, data: dict):
        await self.setup_chat(data, query.from_user)
