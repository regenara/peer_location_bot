import asyncio

from aiogram import executor

import handlers
from data.config import localization_texts
from misc import bot
from misc import dp
from misc import intra_requests_stalking
from misc import mongo

delay = 900


async def send_notifications():
    cursor = await mongo.get_intra_users()
    for document in await cursor.to_list(length=100):
        nickname = document['nickname']
        location = document['location']
        stalkers = document['stalkers']
        access_token = intra_requests_stalking.get_token()
        info = intra_requests_stalking.get_user(nickname, access_token)
        current_location = info['location']
        if current_location != location:
            await mongo.update_intra_user(nickname, {'$set': {'location': current_location}})
            if current_location is not None:
                for user_id in stalkers:
                    lang = await mongo.get_lang(user_id)
                    text = eval(localization_texts['in_campus'][lang])
                    await bot.send_message(user_id, text)


def repeat(coro, loop):
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(delay, repeat, coro, loop)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.call_later(delay, repeat, send_notifications, loop)
    executor.start_polling(dp, loop=loop)
