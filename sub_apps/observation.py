import asyncio
from datetime import datetime
import logging
from typing import (List,
                    Tuple)

from db_models import db
from db_models.peers import Peer
from db_models.users import User
from db_models.users_peers import (Relationship,
                                   UserPeer)
from models.localization import Localization
from utils.intra_api import (IntraAPI,
                             NotFoundIntraError,
                             UnknownIntraError)
from utils.cache import Cache


class Observation:
    def __init__(self, intra: IntraAPI, local: Localization):
        self._intra = intra
        self._local = local
        self._logger = logging.getLogger('Observation')

    @staticmethod
    async def _get_observables(limit: int, offset: int) -> List[Tuple[str, List[int]]]:
        return await db.select([Peer.login, db.func.array_agg(UserPeer.user_id)]).select_from(
            Peer.join(UserPeer)).where(UserPeer.relationship == Relationship.observable).limit(limit).offset(
            offset).group_by(Peer.id).gino.all()

    async def _mailing(self, user_ids: List[int], login: str, current_location: str):
        from utils.helpers import AdminProcesses

        mailing = AdminProcesses(logger=self._logger).mailing
        for user_id in user_ids:
            self._logger.info('Trying to send notification | %s | %s', login, user_id)
            user_data = await User.get_user_data(user_id=user_id)
            if user_data:
                _, peer, user = user_data
                if isinstance(user, dict):
                    user = User.from_dict(data=user)
                    peer = Peer.from_dict(data=peer)
                text = self._local.in_campus.get(user.language, login=login,
                                                 current_location=current_location)
                await mailing(message=text, user=user, peer_id=peer.id)
            else:
                self._logger.error('User not found | %s', user_id)

    async def _observation_process(self, observables: List[Tuple[str, List[int]]]):
        for login, user_ids in observables:
            try:
                self._logger.info('Start observation process | %s', login)
                try:
                    peer = await self._intra.get_peer(login=login)
                except (NotFoundIntraError, UnknownIntraError) as e:
                    self._logger.error('Error response | %s | %s | continue next', login, e)
                    continue
                if peer:
                    location = await Cache().get(key=f'Location:{login}')
                    current_location = peer['location'] or 'not on campus'
                    triggers = (current_location != 'not on campus',
                                location is not None,
                                location != current_location)
                    if triggers[-1]:
                        self._logger.info('Update location | %s | %s → %s', login, location, current_location)
                        await Cache().set(key=f'Location:{login}', value=current_location)
                    if all(triggers):
                        await self._mailing(user_ids=user_ids, login=login, current_location=current_location)
                    self._logger.info('Complete observation process | %s', login)

            except Exception as e:
                self._logger.error('Unknown observation error | %s | %s', login, e)

    async def observation(self):
        while True:
            now = datetime.now()
            offset = 0
            observables = await self._get_observables(limit=100, offset=offset)
            while observables:
                self._logger.info('Start observation for offset=%s', offset)
                await self._observation_process(observables=observables)
                offset += 100
                observables = await self._get_observables(limit=100, offset=offset)
            self._logger.info('Completed observation')
            passed_seconds = (datetime.now() - now).seconds
            if passed_seconds < 600:
                sleep = 600 - passed_seconds
                self._logger.info('Sleep %s seconds after observation', sleep)
                await asyncio.sleep(sleep)
