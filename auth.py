from contextlib import suppress
from urllib.parse import urlparse
import base64

from aiogram.utils.exceptions import MessageToDeleteNotFound
from aiohttp import web

from data.config import CLIENTS_SECRET
from data.config import CLIENT_ID
from data.config import LOCALIZATION_TEXTS
from data.config import REDIRECT_URI
from misc import bot
from misc import dp
from misc import intra_requests
from misc import mongo
from models.peer import Peer
from services.keyboards import language_keyboard
from services.states import States


class Auth:
    def __init__(self, data: dict):
        self.data = data

    async def authorization(self):
        code = self.data['code']
        state = base64.b16decode(self.data["state"]).decode()
        message_id, user_id = state.split('-')
        message_id = int(message_id)
        user_id = int(user_id)
        state = await dp.current_state(user=user_id).get_state()
        if state == States.AUTH:
            grant_type = 'authorization_code'
            js = await intra_requests.request_token(0, CLIENT_ID, CLIENTS_SECRET, grant_type, code)
            access_token = js.get('access_token')
            if access_token:
                peer_data = await intra_requests.request('me', access_token=access_token)
                peer = Peer.short_data(peer_data)
                await mongo.update('users', {'nickname': peer.nickname},
                                   'set', {'nickname': None, 'intra_id': None})
                data = await mongo.update('users', {'user_id': user_id}, 'set',
                                          {'nickname': peer.nickname, 'intra_id': peer.intra_id,
                                           'campus': peer.campus, 'campus_id': peer.campus_id,
                                           'time_zone': peer.time_zone}, upsert=True, return_document=True)
                user = await bot.get_chat(user_id)
                await mongo.update('peers', {'nickname': peer.nickname},
                                   'set', {'nickname': peer.nickname, 'intra_id': peer.intra_id,
                                           'campus': peer.campus, 'campus_id': peer.campus_id,
                                           'time_zone': peer.time_zone, 'username': user.username,
                                           'user_id': user.id}, upsert=True)
                lang = data.get('settings', {}).get('lang') or 'en'
                text = LOCALIZATION_TEXTS['language'][lang].format(nickname=peer.nickname)
                with suppress(MessageToDeleteNotFound):
                    await bot.delete_message(user_id, message_id)
                await bot.send_message(user_id, text, reply_markup=language_keyboard())
                await dp.current_state(user=user_id).finish()
                return True
            return False
        raise web.HTTPForbidden


async def authorize(request):
    if request.query.get('code') and request.query.get('state'):
        data = {'code': request.query['code'], 'state': request.query['state']}
        auth = Auth(data)
        status = await auth.authorization()
        if status:
            return web.HTTPFound('https://profile.intra.42.fr/')
        raise web.HTTPInternalServerError
    raise web.HTTPForbidden


app = web.Application()
app.add_routes([web.get('/', authorize)])

web.run_app(app, host=urlparse(REDIRECT_URI).hostname)
