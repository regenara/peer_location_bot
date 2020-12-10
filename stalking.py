import asyncio
from os import path

from services.utils import read_json
from misc import bot
from services.intra_requests import IntraRequests
from services.mongo import Mongo

config = read_json(path.join('data', 'data.json'))
mongo_username = config['mongo_username']
mongo_password = config['mongo_password']
stalker_client_secret = config['stalker_client_secret']
stalker_client_id = config['stalker_client_id']

localization_texts = read_json(path.join('data', "localization.json"))

intra_requests = IntraRequests(stalker_client_id, stalker_client_secret)
mongo = Mongo(mongo_username, mongo_password)


async def send_notifications():
    cursor = await mongo.get_intra_users()
    for document in await cursor.to_list(length=100):
        nickname = document['nickname']
        location = document['location']
        stalkers = document['stalkers']
        access_token = intra_requests.get_token()
        info = intra_requests.get_user(nickname, access_token)
        current_location = info['location']
        if current_location != location:
            await mongo.update_intra_user(nickname, {'$set': {'location': current_location}})
            if current_location is not None:
                for user_id in stalkers:
                    lang = await mongo.get_lang(user_id)
                    text = eval(localization_texts['in_campus'][lang])
                    await bot.send_message(user_id, text)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(send_notifications())
