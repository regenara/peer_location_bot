import asyncio
from datetime import (datetime,
                      timezone)
import logging
from typing import (Dict,
                    List,
                    Tuple)

from db_models import db
from db_models.peers import Peer
from db_models.users import (User,
                             Languages)
from db_models.campuses import Campus
from db_models.users_peers import (Relationship,
                                   UserPeer)
from models.event import Event
from models.localization import Localization
from utils.intra_api import (IntraAPI,
                             NotFoundIntraError,
                             TimeoutIntraError,
                             UnknownIntraError)
from utils.cache import Cache


class Observation:
    def __init__(self, intra: IntraAPI, local: Localization):
        from utils.helpers import AdminProcesses
        self._intra = intra
        self._local = local
        self._logger = logging.getLogger('Observation')
        self._mailing = AdminProcesses(logger=self._logger).mailing

    @staticmethod
    async def _get_observables(limit: int, offset: int) -> List[Tuple[str, List[int]]]:
        return await db.select([Peer.login, db.func.array_agg(UserPeer.user_id)]).select_from(
            Peer.join(UserPeer)).where(UserPeer.relationship == Relationship.observable).limit(limit).offset(
            offset).group_by(Peer.id).gino.all()

    @staticmethod
    async def _get_notifiable(limit: int, offset: int) -> Tuple[int, int, str, List[int]]:
        query = db.select(
            [Peer.campus_id, Peer.cursus_id, Campus.time_zone, db.func.array_agg(User.id)]).select_from(
            Peer.join(User).join(Campus)).where(
            (User.notify.is_(True)) & (Peer.cursus_id.isnot(None)) & (Peer.campus_id.isnot(None))
        ).limit(limit).offset(offset).order_by(Peer.campus_id, Peer.cursus_id)
        return await query.group_by(Peer.campus_id, Peer.cursus_id, Campus.time_zone).gino.first()

    async def _mailing_observations(self, user_ids: List[int], login: str, location: str, left_peer: bool = False):
        for user_id in user_ids:
            self._logger.info('Trying to send notification | %s | %s', login, user_id)
            user_data = await User.get_user_data(user_id=user_id)
            if user_data:
                _, peer, user = user_data
                if left_peer and user.left_peer:
                    text = self._local.left_workplace.get(user.language, login=login, old_location=location)
                    await self._mailing(message=text, user=user, peer_id=peer.id)
                text = self._local.in_campus.get(user.language, login=login, current_location=location)
                await self._mailing(message=text, user=user, peer_id=peer.id)
            else:
                self._logger.error('User not found | %s', user_id)

    async def _mailing_events_notify(self, texts: Dict[Languages, str], user_ids: List[int]):
        for user_id in user_ids:
            user_data = await User.get_user_data(user_id=user_id)
            self._logger.info('Trying to send event notification | %s ', user_id)
            if user_data:
                _, peer, user = user_data
                text = texts[Languages(user.language)]
                await self._mailing(message=text, user=user, peer_id=peer.id)
            else:
                self._logger.error('User not found | %s', user_id)

    async def _observation_process(self, observables: List[Tuple[str, List[int]]]):
        for login, user_ids in observables:
            try:
                self._logger.info('Start observation process | %s', login)
                try:
                    peer = await self._intra.get_peer(login=login)
                except (NotFoundIntraError, TimeoutIntraError, UnknownIntraError) as e:
                    self._logger.error('Error response | %s | %s | continue next', login, e)
                    continue
                if peer:
                    location = await Cache().get(key=f'Location:{login}')
                    current_location = peer['location'] or 'not on campus'
                    triggers = (current_location != 'not on campus',
                                location is not None,
                                location != current_location)
                    left_triggers = (current_location == 'not on campus',
                                     location != 'not on campus',
                                     location is not None)
                    if triggers[-1]:
                        self._logger.info('Update location | %s | %s → %s', login, location, current_location)
                        await Cache().set(key=f'Location:{login}', value=current_location)
                    if all(triggers):
                        await self._mailing_observations(user_ids=user_ids, login=login,
                                                         location=current_location)
                    elif all(left_triggers):
                        await self._mailing_observations(user_ids=user_ids, login=login,
                                                         location=location, left_peer=True)

                    self._logger.info('Complete observation process | %s', login)

            except Exception as e:
                self._logger.error('Unknown observation error | %s | %s', login, e)

    async def _events_notify_process(self, notifiable: Tuple[int, int, str, List[int]]):
        from utils.text_compile import text_compile

        campus_id, cursus_id, time_zone, user_ids = notifiable
        try:
            self._logger.info('Start notify process | campus=%s | cursus=%s', campus_id, cursus_id)
            try:
                events_data = await self._intra.get_events(campus_id=campus_id, cursus_id=cursus_id)
                exams_data = await self._intra.get_exams(campus_id=campus_id, cursus_id=cursus_id)
                events_data.extend(exams_data)
            except (NotFoundIntraError, TimeoutIntraError, UnknownIntraError) as e:
                self._logger.error('Error response | campus=%s | cursus=%s| %s | return', campus_id, cursus_id, e)
                return
            events = sorted(Event().from_list(events_data=events_data), key=lambda event: event.begin_at)
            for event in events:
                self._logger.info('Start notify | %s | %s | %s', event.id, event.name, event.kind)
                cache_event = await Cache().get(key=f'Event:{event.kind}:{event.id}:{campus_id}.{cursus_id}')
                if not cache_event:
                    texts = {}
                    for language in (Languages.ru, Languages.en):
                        title = self._local.new_event.get(language)
                        text = text_compile.event_compile(event=event, language=language, time_zone=time_zone)
                        texts.update({language: title + text})
                    await self._mailing_events_notify(texts=texts, user_ids=user_ids)
                    ttl = (datetime.fromisoformat(event.begin_at.replace('Z', '+00:00')) -
                           datetime.now(tz=timezone.utc)).total_seconds() + 300
                    await Cache().set(key=f'Event:{event.kind}:{event.id}:{campus_id}.{cursus_id}',
                                      value=True, ttl=int(ttl))
                    self._logger.info('Update notify | %s | %s | %s', event.id, event.name, event.kind)
                else:
                    self._logger.info('Skip notify | %s | %s | %s', event.id, event.name, event.kind)

        except Exception as e:
            self._logger.error('Unknown notify error | campus=%s | cursus=%s | %s', campus_id, cursus_id, e)

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

    async def event_notify(self):
        while True:
            offset = 0
            notifiable = await self._get_notifiable(limit=1, offset=offset)
            while notifiable:
                self._logger.info('Start event notify for offset=%s', offset)
                await self._events_notify_process(notifiable=notifiable)
                offset += 1
                notifiable = await self._get_notifiable(limit=1, offset=offset)
            self._logger.info('Completed event notify, sleep 1800 seconds')
            await asyncio.sleep(1800)
