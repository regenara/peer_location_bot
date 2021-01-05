import asyncio

from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorCursor

import misc


class Mongo:
    def __init__(self, mongo_username: str, mongo_password: str):
        sign_in = f'mongodb+srv://{mongo_username}:' \
                  f'{mongo_password}@cluster0-habpf.mongodb.net/test?retryWrites=true&w=majority'
        client = AsyncIOMotorClient(sign_in).intragram
        self.intra_users = client['intra_users']
        self.intra_projects = client['projects']
        self.tg_users = client['tg_users']

    async def tg_db_fill(self, user_id: int):
        data = {'user_id': user_id, 'settings': {'avatar': True, 'lang': 'en', 'results_count': 15},
                'friends': [], 'notifications': []}
        self.tg_users.insert_one(data)

    async def intra_db_fill(self, nickname: str, location: str):
        data = {'nickname': nickname, 'location': location, 'stalkers': []}
        self.intra_users.insert_one(data)

    async def find_tg_user(self, user_id: int) -> dict:
        data = await self.tg_users.find_one({'user_id': user_id})
        if data is None:
            await self.tg_db_fill(user_id)
            await asyncio.sleep(1)
            data = await self.tg_users.find_one({'user_id': user_id})
        return data

    async def find_intra_user(self, nickname: str, location: str = None) -> dict:
        data = await self.intra_users.find_one({'nickname': nickname})
        if data is None:
            await self.intra_db_fill(nickname, location)
            data = await self.intra_users.find_one({'nickname': nickname})
        return data

    async def update_tg_user(self, user_id: int, data: dict):
        await self.tg_users.find_one_and_update({'user_id': user_id}, data)

    async def update_intra_user(self, nickname: str, data: dict):
        await self.intra_users.find_one_and_update({'nickname': nickname}, data)

    async def get_count(self, user_id: int, type_count: str) -> int:
        data = await self.find_tg_user(user_id)
        count = len(data[type_count])
        return count

    async def get_lang(self, user_id) -> str:
        data = await self.find_tg_user(user_id)
        lang = data['settings']['lang']
        return lang

    async def get_results_count(self, user_id: int) -> int:
        data = await self.find_tg_user(user_id)
        results_count = data['settings'].get('results_count')
        if results_count is None:
            await self.update_tg_user(user_id, {'$set': {'settings.results_count': 15}})
            results_count = 15
        return results_count

    async def get_project(self, project_id) -> dict:
        data = await self.intra_projects.find_one({'project_id': project_id})
        if data is None:
            project = misc.intra_requests.get_project(project_id)
            data = {'project_id': project['id'], 'name': project['name'], 'slug': project['slug']}
            self.intra_projects.insert_one(data)
            await asyncio.sleep(1)
        return data

    async def get_intra_users(self) -> AsyncIOMotorCursor:
        cursor = self.intra_users.find({})
        return cursor

    async def get_tg_users(self) -> AsyncIOMotorCursor:
        cursor = self.tg_users.find({})
        return cursor
