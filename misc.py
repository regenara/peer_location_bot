import logging

from aiogram import Bot
from aiogram import Dispatcher
from aiogram import types
from aiogram.contrib.fsm_storage.redis import RedisStorage

from data.config import API_TOKEN
from data.config import CLIENTS
from data.config import MONGO_PASSWORD
from data.config import MONGO_USERNAME
from services.intra_requests import IntraRequests
from services.mongo import Mongo

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
storage = RedisStorage('localhost', 6379, db=5)
dp = Dispatcher(bot, storage=storage)


logging.basicConfig(level=logging.INFO)
intra_requests = IntraRequests(CLIENTS)
mongo = Mongo(MONGO_USERNAME, MONGO_PASSWORD)
