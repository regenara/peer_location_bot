import logging

from aiogram.dispatcher.webhook import configure_app
from aiohttp import web

import handlers
import services.middleware
from config import Config

from misc import (bot,
                  dp)
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


async def on_startup(app):
    await Config.start()
    webhook = await bot.get_webhook_info()
    if webhook.url != Config.webhook_url:
        if not webhook.url:
            await bot.delete_webhook()
        await bot.set_webhook(Config.webhook_url)


async def on_shutdown(app):
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()
    await Config.stop()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(name)s %(module)s - %(funcName)s: %(message)s')
    disabled_loggers = ['gino.engine._SAEngine', 'aiogram', 'aiocache.base']
    for logger_name in disabled_loggers:
        logging.getLogger(logger_name).disabled = True
    logger = logging.getLogger('bot')

    web_server = WebServer()
    services.setup(dp)

    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    app.add_routes([web.get('/', web_server.authorization),
                    web.post('/webhooks/donate', web_server.donate_stream_webhook)])
    configure_app(dp, app, '/webhooks/bot')
    web.run_app(app, host='localhost', port=8081)
