import asyncio

from models.localization import Localization
from utils.intra_api import IntraAPI

from .observation import Observation
from .updater import Updater


class SubApps:
    def __init__(self, intra: IntraAPI, local: Localization):
        self.running = []
        self.stalking = Observation(intra=intra, local=local)
        self.updater = Updater(intra=intra)

    async def start(self):
        self.running.append(asyncio.create_task(self.stalking.observation()))
        self.running.append(asyncio.create_task(self.updater.updater()))

    async def stop(self):
        for task in self.running:
            task.cancel()
