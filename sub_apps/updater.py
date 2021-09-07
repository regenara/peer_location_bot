import asyncio
import logging

from db_models.campuses import Campus
from utils.cache import Cache
from utils.intra_api import (IntraAPI,
                             NotFoundIntraError,
                             UnknownIntraError)


class Updater:
    def __init__(self, intra: IntraAPI):
        self._intra = intra
        self._logger = logging.getLogger('Updater')

    async def _campuses_updater(self):
        await Cache().delete(key='Campus.get_campuses')
        campuses_db = await Campus.get_campuses()
        try:
            campuses = await self._intra.get_campuses()
        except UnknownIntraError as e:
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
                except (NotFoundIntraError, UnknownIntraError) as e:
                    self._logger.error('Get campus=%s error %s', campus_id, e)

    async def updater(self):
        while True:
            self._logger.info('Start updater')
            await self._campuses_updater()
            self._logger.info('Sleep 86400 seconds after updater')
            await asyncio.sleep(86400)
