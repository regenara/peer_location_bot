from motor.motor_asyncio import AsyncIOMotorClient

import config


sign_in = f'mongodb+srv://{config.mongo_username}' \
          f':{config.mongo_password}@cluster0-habpf.mongodb.net/test?retryWrites=true&w=majority'

client = AsyncIOMotorClient(sign_in).intragram

intra_users = client['intra_users']
user_settings = client['user_settings']


async def find_tg_user(user_id):
    data = await user_settings.find_one({'user_id': user_id})
    return data


async def update(user_id, data):
    await user_settings.find_one_and_update({'user_id': user_id}, data)


async def db_fill(user_id, lang):
    if lang not in ('ru', 'en'):
        lang = 'en'
    data = {'user_id': user_id, 'settings': {'avatar': True, 'lang': lang}, 'friends': {}}
    user_settings.insert_one(data)

