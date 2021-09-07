from aiogram import types
from aiogram.bot.bot import Bot
from aiogram.contrib.fsm_storage.redis import RedisStorage
from aiogram.dispatcher.dispatcher import Dispatcher

from config import Config

bot = Bot(token=Config.api_token, parse_mode=types.ParseMode.HTML)
storage = RedisStorage(db=5)
dp = Dispatcher(bot, storage=storage)
