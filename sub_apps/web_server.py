import logging
from json.decoder import JSONDecodeError
from typing import (Any,
                    Dict,
                    Tuple)

from aiohttp import (web,
                     web_request)
from aiogram.utils.markdown import (hbold,
                                    hcode,
                                    hitalic)
from aiogram.utils.exceptions import (MessageCantBeDeleted,
                                      MessageToDeleteNotFound)
from asyncpg.exceptions import UniqueViolationError

from config import Config
from db_models import db
from db_models.donate import Donate
from db_models.peers import Peer
from db_models.users import User
from db_models.users_peers import UserPeer
from services.keyboards import (menu_keyboard,
                                settings_keyboard)
from services.states import States
from misc import (dp,
                  bot)
from utils.cache import (Cache,
                         del_cache)
from utils.intra_api import UnknownIntraError
from utils.savers import Savers


class WebServer:
    def __init__(self):
        self._logger = logging.getLogger('AuthServer')

    @del_cache(keys=['Donate.get_last_month_donate', 'Donate.get_top_donaters'], without_sub_key=[0, 1])
    async def _data_from_webhook(self, webhook_data: Dict[str, Any]) -> Tuple[bool, int]:
        try:
            uid = webhook_data['uid']
            nickname = webhook_data['nickname'].strip()
            sum_ = float(webhook_data['sum'])
            message = webhook_data['message']
            await Donate.create(uid=uid, nickname=nickname, sum=sum_, message=message)
            self._logger.info('Successful save donate | %s', webhook_data)
            await bot.send_message(Config.admin, '\n\n'.join((f'Донат от {hbold(nickname)} на сумму {hcode(sum_)}руб',
                                                              hitalic(message) if message else "")))
            return True, 200
        except KeyError as e:
            self._logger.error('Failed get data from donate | %s | %s', webhook_data, e)
        except UniqueViolationError as e:
            self._logger.error('Failed save donate data | %s | %s', webhook_data, e)
        return False, 400

    @staticmethod
    async def _get_peer(peer_data: Dict[str, Any], user_id: int) -> Peer:
        campus_id = [campus['campus_id'] for campus in peer_data['campus_users'] if campus['is_primary']][0]
        return await Savers.get_peer(peer_id=peer_data['id'], login=peer_data['login'],
                                     campus_id=campus_id, user_id=user_id)

    async def _relationships_transfer(self, new_user_id: int, user_from_peer: User):
        if user_from_peer:
            async with db.transaction():
                await UserPeer.update.values(
                    user_id=new_user_id).where(UserPeer.user_id == user_from_peer.id).gino.status()
            await Cache().delete(key=f'UserPeer._get_relationships:{user_from_peer.id}')
            self._logger.info('Successful transfer relationships | %s', new_user_id)

    async def _create_user(self, new_user_id: int, language_code: str, peer_id: int,
                           user_from_peer: User) -> Tuple[User, str]:
        keys = [f'User.get_user_from_peer:{peer_id}', f'User.get_user_data:{new_user_id}']
        if user_from_peer:
            keys.append(f'User.get_user_data:{user_from_peer.id}')
            if user_from_peer.username:
                keys.append(f'User.get_login_from_username:{user_from_peer.username.lower()}')
        user = await bot.get_chat(chat_id=new_user_id)
        user_from_id = await User.get(new_user_id)
        show_avatar = user_from_peer.show_avatar if user_from_peer else False
        show_me = user_from_peer.show_me if user_from_peer else False
        use_default_campus = user_from_peer.use_default_campus if user_from_peer else True
        language_code = user_from_peer.language if user_from_peer else language_code
        if not user_from_id:
            new_user = await User.create_user(user_id=new_user_id, username=user.username, language=language_code,
                                              show_avatar=show_avatar, show_me=show_me,
                                              use_default_campus=use_default_campus)
            self._logger.info('Successful create | %s ', user.username or new_user_id)
        else:
            await user_from_id.update(username=user.username, show_avatar=show_avatar, show_me=show_me,
                                      language=language_code, use_default_campus=use_default_campus).apply()
            new_user = await User.get(new_user_id)
            self._logger.info('Successful update user | %s', user.username or new_user_id)
        [await Cache().delete(key=key) for key in keys]
        return new_user, language_code

    async def _authorization_process(self, code: str, state: str) -> bool:
        signature = Config.fernet.decrypt(state.encode('utf-8')).decode('utf-8')
        try:
            message_id, user_id, language_code = signature.split('.')
            message_id, user_id = map(int, (message_id, user_id))
            self._logger.info('Successful parse signature | message_id %s | user_id %s | language_code %s',
                              message_id, user_id, language_code)
        except ValueError:
            self._logger.error('Failed parse signature=%s', signature)
            raise web.HTTPForbidden
        try:
            await bot.delete_message(chat_id=user_id, message_id=message_id)
            self._logger.info('Successful delete message | message_id %s | user_id %s', message_id, user_id)
        except (MessageToDeleteNotFound, MessageCantBeDeleted) as e:
            self._logger.error('Failed delete message | message_id %s | user_id %s | %s', message_id, user_id, e)
        state = await dp.current_state(user=user_id).get_state()
        if state == States.AUTH:
            personal_access_token = await Config.intra.auth(client_id=Config.application.client_id,
                                                            client_secret=Config.application.client_secret,
                                                            code=code)
            try:
                peer = await Config.intra.get_me(personal_access_token=personal_access_token)
            except UnknownIntraError as e:
                self._logger.error('Failed get me | token %s | user_id %s | %s',
                                   personal_access_token, user_id, e)
                raise web.HTTPInternalServerError
            user_from_peer = await User.get_user_from_peer(peer_id=peer['id'])
            user, language_code = await self._create_user(new_user_id=user_id, language_code=language_code,
                                                          peer_id=peer['id'], user_from_peer=user_from_peer)
            peer = await self._get_peer(peer_data=peer, user_id=user_id)
            await self._relationships_transfer(new_user_id=user_id, user_from_peer=user_from_peer)
            await dp.current_state(user=user_id).set_state(States.GRANTED)
            await bot.send_message(user_id, text=Config.local.hello.get(language_code, login=peer.login),
                                   reply_markup=menu_keyboard(language=language_code))
            await bot.send_message(user_id,
                                   Config.local.help_text.get(language_code, cursus=Config.courses[Config.cursus_id]),
                                   reply_markup=settings_keyboard(user=user))
            self._logger.info('Successful user authorization | user_id %s | login %s',
                              user_id, peer.login)
            return True
        self._logger.error('Incorrect state=%s', state)

    async def authorization(self, request: web_request.Request):
        if request.query.get('code') and request.query.get('state'):
            code = request.query['code']
            state = request.query['state']
            self._logger.info('Successful get query | code %s | state %s', code, state)
            status = await self._authorization_process(code=code, state=state)
            if status:
                return web.HTTPFound('https://profile.intra.42.fr/')
            raise web.HTTPForbidden
        self._logger.error('Failed get code and state, redirect to bot')
        return web.HTTPFound('https://t.me/peer_location_bot')

    async def donate_stream_webhook(self, request: web_request.Request):
        try:
            webhook_data = await request.json()
            is_success, status = await self._data_from_webhook(webhook_data=webhook_data)
        except JSONDecodeError as e:
            self._logger.error('Failed get json from request | %s', e)
            is_success, status = False, 400
        return web.json_response({'success': is_success}, status=status)
