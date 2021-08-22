from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorCursor

# TODO в будущем перейти на PostgreSQL


class Mongo:
    def __init__(self, mongo_username: str,
                 mongo_password: str):
        sign_in = f'mongodb+srv://{mongo_username}:' \
                  f'{mongo_password}@cluster0-habpf.mongodb.net/test?retryWrites=true&w=majority'
        client = AsyncIOMotorClient(sign_in).intragram

        self.databases = {'peers': client['intra_users'], 'projects': client['projects'],
                          'users': client['tg_users'], 'campuses': client['campuses'],
                          'coalitions': client['coalitions'], 'projects42': client['projects42']}

    async def insert(self, db: str, data: dict):
        await self.databases[db].insert_one(data)

    async def insert_many(self, db: str, data: list):
        await self.databases[db].insert_many(data)

    async def find(self, db: str, find: dict) -> dict:
        collection = await self.databases[db].find_one(find)
        return collection

    async def update(self, db: str, find: dict, operator: str, data: dict, upsert=False,
                     return_document=False) -> dict:
        return await self.databases[db].find_one_and_update(find, {f'${operator}': data},
                                                            upsert=upsert, return_document=return_document)

    async def get_collections(self, db: str) -> AsyncIOMotorCursor:
        return self.databases[db].find({})

    async def delete(self, db: str, find: dict):
        await self.databases[db].delete_one(find)

    async def delete_all(self, db: str):
        await self.databases[db].delete_many({})
