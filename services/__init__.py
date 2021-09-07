from aiogram import Dispatcher
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from services.middleware import Middleware


def setup(dispatcher: Dispatcher):
    dispatcher.middleware.setup(LoggingMiddleware("bot"))
    dispatcher.middleware.setup(Middleware())
