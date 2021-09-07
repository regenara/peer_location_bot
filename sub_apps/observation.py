import asyncio
from datetime import datetime
import logging
from typing import List

from aiogram.utils.exceptions import (BotBlocked,
                                      ChatNotFound,
                                      UserDeactivated)

from db_models import db
from db_models.peers import Peer
from db_models.users import User
from db_models.users_peers import (Relationship,
                                   UserPeer)
from models.localization import Localization
from utils.intra_api import (IntraAPI,
                             NotFoundIntraError,
                             UnknownIntraError)
from utils.cache import (Cache,
                         cache)


class Observation:
    def __init__(self, intra: IntraAPI, local: Localization):
        self._intra = intra
        self._local = local
        self._logger = logging.getLogger('Observation')

    @cache(ttl=3600)
    async def _get_observables(self, limit: int, offset: int) -> List[list]:
        observables = await db.select([Peer.login, db.func.array_agg(UserPeer.user_id)]).select_from(
            Peer.join(UserPeer)).where(UserPeer.relationship == Relationship.observable).limit(limit).offset(
            offset).group_by(Peer.id).gino.all()
        return [list(observable) for observable in observables]

    async def _send_notifications(self, observables: List[list]):
        from misc import bot

        for login, user_ids in observables:
            try:
                peer = await self._intra.get_peer(login=login)
            except (NotFoundIntraError, UnknownIntraError) as e:
                self._logger.error('Response exception=%s %s, continue next', login, e)
                continue
            if peer:
                location = await Cache().get(key=f'Location:{login}')
                current_location = peer['location'] or 'not on campus'
                if location != current_location:
                    self._logger.info('Update peer=%s location=%s', login, current_location)
                    await Cache().set(key=f'Location:{login}', value=current_location)

                truths = (current_location != 'not on campus', location is not None, location != current_location)
                if all(truths):
                    for user_id in user_ids:
                        *_, user = await User.get_user_data(user_id=user_id)
                        if isinstance(user, dict):
                            user = User.from_dict(data=user)
                        try:
                            text = self._local.in_campus.get(user.language, login=login,
                                                             current_location=current_location)
                            await bot.send_message(chat_id=user_id, text=text)
                            self._logger.info('Send notification=%s %s',
                                              login, user.username or user.id)
                            await asyncio.sleep(0.1)

                        except (BotBlocked, UserDeactivated) as e:
                            await user.delete()
                            self._logger.error('BotBlocked or UserDeactivated user=%s %s, user deleted',
                                               user.username or user.id, e)

                        except ChatNotFound as e:
                            self._logger.error('ChatNotFound user=%s %s',
                                               user.username or user.id, e)

    async def observation(self):
        while True:
            self._logger.info('Start observation')
            now = datetime.now()
            offset = 0
            observables = await self._get_observables(limit=100, offset=offset)
            while observables:
                await self._send_notifications(observables=observables)
                offset += 100
                observables = await self._get_observables(limit=100, offset=offset)
            passed_seconds = (datetime.now() - now).seconds
            if passed_seconds < 600:
                sleep = 600 - passed_seconds
                self._logger.info('Sleep %s seconds after observation', sleep)
                await asyncio.sleep(sleep)
