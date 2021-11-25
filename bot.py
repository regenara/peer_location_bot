import logging
from urllib.parse import urljoin

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
                              IsBackToCampuses)
from sub_apps.web_server import WebServer

for custom_filter in (IsIntrovert,
                      IsUnauthorized,
                      IsRemoveFriend,
                      IsMailing,
                      IsUpdateProjects,
                      IsBackToCourses,
                      IsBackToCampusesFromCourses,
                      IsBackToCampuses):
    dp.filters_factory.bind(custom_filter)


async def on_startup(app):
    await Config.start()
    await Config.sub_apps.start()
    webhook = await bot.get_webhook_info()
    webhook_url = urljoin(Config.bot_base_url, Config.webhook_bot_path)
    if webhook.url != webhook_url:
        if not webhook.url:
            await bot.delete_webhook()
        await bot.set_webhook(webhook_url)


async def on_shutdown(app):
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()
    await Config.sub_apps.stop()
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
                    web.post(Config.webhook_donate_path, web_server.donate_stream_webhook)])
    configure_app(dp, app, Config.webhook_bot_path)
    web.run_app(app, host='localhost', port=8081)
