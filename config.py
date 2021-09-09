from os import getenv
from typing import Dict

import ujson
from aiocache import Cache
from aiocache.backends.redis import RedisCache
from cryptography.fernet import Fernet

import db_models
from db_models.applications import Application
from db_models.courses import Courses
from models.localization import Localization
from sub_apps.sub_apps import SubApps
from utils.intra_api import IntraAPI


def read_json(path_to_file: str) -> Dict[str, str]:
    with open(path_to_file) as f:
        data = ujson.load(f)
    return data


class Config:
    admin: int = int(getenv('ADMIN', '373749366'))
    api_token: str = getenv('API_TOKEN')
    webhook_url: str = getenv('WEBHOOK_URL')

    fernet: Fernet = None
    salt: str = getenv('SALT', '5j3I1xNcCpo2ZfFAkVMVpk6mRMpBmXqWXU7udHUgFtY=')

    db_url = getenv('DB_URL', 'driver://user:pass@localhost/dbname')
    db: db_models.Gino = db_models.db
    redis_url = getenv('REDIS_URL', 'redis://localhost:6379')
    redis: RedisCache = None

    redirect_uri = getenv('REDIRECT_URI', 'http://localhost:8081/')
    test = str(getenv('TEST', True)).lower() == 'true'
    intra: IntraAPI = None
    application: Application = None
    courses: Dict[int, str] = None
    cursus_id: int = None

    sub_apps: SubApps = None

    localization = getenv('LOCALIZATION', 'localization.json')
    local: Localization = None

    @classmethod
    async def start(cls):
        cls.fernet = Fernet(cls.salt.encode())
        await db_models.db.set_bind(bind=cls.db_url, min_size=1)
        cls.redis = Cache.from_url(cls.redis_url)
        cls.application = await Application.get_main() if not cls.test else await Application.get_test()
        cls.intra = IntraAPI(config=cls)
        await cls.intra.load()
        courses = await Courses.get_courses()
        cls.courses = {cursus.id: cursus.name for cursus in courses}
        cls.cursus_id = [cursus.id for cursus in courses if cursus.is_primary][0]
        cls.local = Localization()
        cls.local.load(data=read_json(cls.localization))
        cls.sub_apps = SubApps(intra=cls.intra, local=cls.local)

    @classmethod
    async def stop(cls):
        await cls.db.pop_bind().close()
        await cls.redis.close()
        await cls.intra.session.close()
