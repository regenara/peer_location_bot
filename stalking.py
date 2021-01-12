import asyncio
from contextlib import suppress

from aiogram.utils.exceptions import ChatNotFound
from aiogram.utils.exceptions import BotBlocked
from aiogram.utils.exceptions import UserDeactivated

from data.config import localization_texts
from misc import bot
from misc import intra_requests
from misc import mongo


async def send_notifications():
    cursor = await mongo.get_intra_users()
    documents = await cursor.to_list(length=100)
    while documents:
        for document in documents:
            nickname = document['nickname']
            location = document['location']
            stalkers = document['stalkers']
            if stalkers:
                info = intra_requests.get_user(nickname)
                current_location = info['location']
                if current_location != location:
                    await mongo.update_intra_user(nickname, {'$set': {'location': current_location}})
                    if current_location is not None:
                        for user_id in stalkers:
                            lang = await mongo.get_lang(user_id)
                            text = localization_texts['in_campus'][lang].format(nickname=nickname,
                                                                                current_location=current_location)
                            with suppress(ChatNotFound, BotBlocked, UserDeactivated):
                                await bot.send_message(user_id, text)
                            await asyncio.sleep(0.1)
        documents = await cursor.to_list(length=100)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(send_notifications())
    loop.close()
