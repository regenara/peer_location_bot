import asyncio
import logging
from contextlib import suppress

from aiogram.utils.exceptions import ChatNotFound

from db_models import db
from db_models.campuses import Campus
from db_models.peers import Peer
from db_models.users import User
from services.states import States
from utils.cache import Cache
from utils.intra_api import (IntraAPI,
                             NotFoundIntraError,
                             TimeoutIntraError,
                             UnknownIntraError)


class Updater:
    def __init__(self, intra: IntraAPI):
        self._intra = intra
        self._logger = logging.getLogger('Updater')

    async def _campuses_updater(self):
        self._logger.info('Start campuses updater')
        await Cache().delete(key='Campus.get_campuses')
        campuses_db = await Campus.get_campuses()
        try:
            campuses = await self._intra.get_campuses()
        except (UnknownIntraError, TimeoutIntraError) as e:
            self._logger.error('Get campuses error %s', e)
            return
        if len(campuses_db) < len(campuses):
            campus_db_ids = [campus.id for campus in campuses_db]
            campus_ids = [campus['id'] for campus in campuses]
            for campus_id in set(campus_ids) - set(campus_db_ids):
                try:
                    campus = await self._intra.get_campus(campus_id=campus_id)
                    await Campus.create_campus(campus_id=campus_id, name=campus['name'],
                                               time_zone=campus['time_zone'])
                    self._logger.info('Save campus %s in db', campus['name'])
                except (NotFoundIntraError, UnknownIntraError, TimeoutIntraError) as e:
                    self._logger.error('Get campus error | %s | %s', campus_id, e)
        self._logger.info('Completed campuses updater')

    async def _usernames_updater(self):
        from misc import bot

        self._logger.info('Start usernames updater')
        async with db.transaction():
            offset = 0
            query = db.select([User, Peer]).select_from(User.outerjoin(Peer)).limit(100).offset(offset).order_by(
                User.id)
            result = await query.gino.load((User, Peer.id)).all()
            while result:
                self._logger.info('Start usernames updater for offset=%s', offset)
                for user_db, peer_id in result:
                    with suppress(ChatNotFound):
                        user = await bot.get_chat(user_db.id)
                        self._logger.info('Check user | %s [%s]', user.id, user.username)
                        keys = []
                        if not user.first_name:
                            keys.extend((
                                f'Peer.get_peer:{peer_id}',
                                f'UserPeer._get_relationships:{user.id}',
                                f'User.get_user_data:{user.id}',
                                f'User.get_user_from_peer:{peer_id}'))
                            await user_db.delete()
                            self._logger.info('User deactivated | %s | user deleted', user.id)
                        elif user.username != user_db.username:
                            keys.extend((
                                f'User.get_user_data:{user.id}',
                                f'User.get_user_from_peer:{peer_id}'
                            ))
                            self._logger.info('Update username | %s → %s', user_db.username, user.username)
                            await user_db.update(username=user.username).apply()
                        else:
                            self._logger.info('User has not changed | %s [%s]', user.id, user.username)
                        [await Cache().delete(key=key) for key in keys]
                offset += 100
                query = db.select([User, Peer]).select_from(
                    User.outerjoin(Peer)).limit(100).offset(offset).order_by(User.id)
                result = await query.gino.load((User, Peer.id)).all()
        self._logger.info('Completed usernames updater')

    async def clear_queue(self):
        from bot import dp
        from config import Config

        while True:
            self._logger.info('Start clear queue')
            queue = Config.queue.copy()
            Config.queue = set()
            for user_id in queue:
                await dp.current_state(user=user_id).set_state(States.GRANTED)
                self._logger.info('Clear queue for user_id %s', user_id)
            self._logger.info('Completed clear queue, sleep 120 seconds')
            await asyncio.sleep(120)

    async def updater(self):
        while True:
            self._logger.info('Start updater')
            await self._campuses_updater()
            await self._usernames_updater()
            self._logger.info('Sleep 86400 seconds after updater')
            await asyncio.sleep(86400)
