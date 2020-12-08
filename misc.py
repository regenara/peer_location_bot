from aiogram import Bot
from aiogram import Dispatcher
from aiogram import types

from config import mongo_username
from config import mongo_password
from config import api_token
from mongo import Mongo

bot = Bot(token=api_token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

mongo = Mongo(mongo_username, mongo_password)
