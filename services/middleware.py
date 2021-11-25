from aiogram.types import (CallbackQuery,
                           Message,
                           User)
from aiogram.dispatcher.middlewares import BaseMiddleware

from utils.cache import Cache


class Middleware(BaseMiddleware):
    async def setup_chat(self, data: dict, user: User):
        from db_models.users import User as UserDB
        from db_models.peers import Peer as PeerDB
        from models.peer import Peer

        user_data = await UserDB.get_user_data(user_id=user.id)
        if user_data:
            updated = False
            if user.username != user_data[-1].username:
                await UserDB.update_user(user_id=user.id, username=user.username)
                updated = True
            peer = await Peer().get_peer(login=user_data[1].login, extended=False)
            if peer.campus_id != user_data[1].campus_id or peer.cursus_id != user_data[1].cursus_id:
                await PeerDB.update_peer(peer_id=peer.id, campus_id=peer.campus_id, cursus_id=peer.cursus_id)
                keys = [f'User.get_user_from_peer:{peer.id}', f'User.get_user_data:{user.id}']
                [await Cache().delete(key=key) for key in keys]
                updated = True
            if updated:
                user_data = await UserDB.get_user_data(user_id=user.id)

        data['user_data'] = user_data

    async def on_pre_process_message(self, message: Message, data: dict):
        await self.setup_chat(data, message.from_user)

    async def on_pre_process_callback_query(self, query: CallbackQuery, data: dict):
        await self.setup_chat(data, query.from_user)
