from motor.motor_asyncio import AsyncIOMotorClient


class Mongo:
    def __init__(self, mongo_username: str, mongo_password: str):
        sign_in = f'mongodb+srv://{mongo_username}:' \
                  f'{mongo_password}@cluster0-habpf.mongodb.net/test?retryWrites=true&w=majority'
        client = AsyncIOMotorClient(sign_in).intragram
        self.intra_users = client['intra_users']
        self.user_settings = client['user_settings']

    async def db_fill(self, user_id: int, lang: str):
        if lang not in ('ru', 'en'):
            lang = 'en'
        data = {'user_id': user_id, 'settings': {'avatar': True, 'lang': lang}, 'friends': {}}
        self.user_settings.insert_one(data)

    async def find_tg_user(self, user_id: int) -> dict:
        data = await self.user_settings.find_one({'user_id': user_id})
        return data

    async def update(self, user_id: int, data: dict):
        await self.user_settings.find_one_and_update({'user_id': user_id}, data)
