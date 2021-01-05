import logging

from aiogram import Bot
from aiogram import Dispatcher
from aiogram import types

from data.config import api_token
from data.config import clients
from data.config import mongo_username
from data.config import mongo_password
from services import filters
from services.intra_requests import IntraRequests
from services.mongo import Mongo

bot = Bot(token=api_token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

for custom_filter in (filters.IsFriends, filters.IsSettings, filters.IsHelp, filters.IsAbout,
                      filters.IsDonate, filters.IsFriendsList, filters.IsMailing):
    dp.filters_factory.bind(custom_filter)

logging.basicConfig(level=logging.INFO)
intra_requests = IntraRequests(clients)
mongo = Mongo(mongo_username, mongo_password)
