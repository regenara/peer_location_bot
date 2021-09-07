import asyncio
import logging

from aiogram.dispatcher.webhook import configure_app
from aiohttp import web

import handlers
import services.middleware
from config import Config

from misc import dp
from services.filters import (IsIntrovert,
                              IsUnauthorized,
                              IsRemoveFriend,
                              IsMailing,
                              IsUpdateProjects,
                              IsBackToCourses,
                              IsBackToCampusesFromCourses,
                              IsBackToCampusesFromLocations)
from sub_apps.web_server import WebServer

for custom_filter in (IsIntrovert,
                      IsUnauthorized,
                      IsRemoveFriend,
                      IsMailing,
                      IsUpdateProjects,
                      IsBackToCourses,
                      IsBackToCampusesFromCourses,
                      IsBackToCampusesFromLocations):
    dp.filters_factory.bind(custom_filter)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(name)s %(module)s - %(funcName)s: %(message)s')
    disabled_loggers = ['gino.engine._SAEngine', 'aiogram', 'aiocache.base']
    for logger_name in disabled_loggers:
        logging.getLogger(logger_name).disabled = True
    logger = logging.getLogger('bot')

    web_server = WebServer()
    services.setup(dp)
    loop_config = asyncio.get_event_loop()
    loop_config.create_task(Config.start())
    loop_polling = asyncio.get_event_loop()
    loop_polling.create_task(dp.start_polling())
    app = web.Application()
    app.add_routes([web.get('/', web_server.authorization),
                    web.post('/webhook', web_server.donate_stream_webhook)])
    configure_app(dp, app)
    web.run_app(app, host='localhost', port=8081)
