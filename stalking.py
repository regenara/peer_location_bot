import asyncio

from aiogram.utils.exceptions import BotBlocked
from aiogram.utils.exceptions import ChatNotFound
from aiogram.utils.exceptions import UserDeactivated

from data.config import LOCALIZATION_TEXTS
from misc import bot
from misc import intra_requests
from misc import mongo
from models.peer import Peer
from models.user import User


async def send_notifications():
    cursor = await mongo.get_collections('peers')
    collections = await cursor.to_list(length=100)
    while collections:
        for collection in collections:
            peer_db = Peer.from_db(collection)
            if peer_db.stalkers:
                peer_data = await intra_requests.get_peer(peer_db.nickname)
                peer = Peer.short_data(peer_data)
                new_data = {}
                if peer_db.intra_id is None:
                    new_data.update({'intra_id': peer.intra_id})
                if peer.location != peer_db.location:
                    new_data.update({'location': peer.location})
                if new_data:
                    await mongo.update('peers', {'nickname': peer_db.nickname}, 'set', new_data)
                if peer.location is not None and peer_db.location != 'not_in_db' and peer.location != peer_db.location:
                    for user_id in peer_db.stalkers:
                        data = await mongo.find('users', {'user_id': user_id})
                        user = User.from_dict(data)
                        text = LOCALIZATION_TEXTS['in_campus'][user.lang].format(nickname=peer.nickname,
                                                                                 current_location=peer.location)
                        try:
                            await bot.send_message(user_id, text)
                            await asyncio.sleep(0.1)
                        except (BotBlocked, UserDeactivated):
                            await mongo.delete('users', {'user_id': user_id})
                        except ChatNotFound:
                            pass
        collections = await cursor.to_list(length=100)
    await intra_requests.session.close()
    await bot.session.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(send_notifications())
    loop.close()
