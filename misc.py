import logging

from aiogram import Bot
from aiogram import Dispatcher
from aiogram import types

from data.config import api_token
from data.config import client_id
from data.config import client_secret
from data.config import mongo_username
from data.config import mongo_password
import services.filters
from services.intra_requests import IntraRequests
from services.mongo import Mongo

bot = Bot(token=api_token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)
dp.filters_factory.bind(services.filters.IsFriendsList)
logging.basicConfig(level=logging.INFO)

intra_requests = IntraRequests(client_id, client_secret)
mongo = Mongo(mongo_username, mongo_password)
