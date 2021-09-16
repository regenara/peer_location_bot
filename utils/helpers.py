import asyncio
import logging
from io import BytesIO
from typing import (Dict,
                    List,
                    Union)

from aiogram.types import Message
from aiogram.utils.exceptions import (BotBlocked,
                                      ChatNotFound,
                                      UserDeactivated)
from aiogram.utils.markdown import hcode
from bs4 import BeautifulSoup

from db_models import db
from db_models.peers import Peer
from db_models.projects import Project
from db_models.users import User
from services.keyboards import menu_keyboard
from misc import bot
from utils.cache import Cache


class AdminProcesses:

    def __init__(self, logger: logging = None):
        from config import Config
        self._config = Config
        self._logger = logger or logging.getLogger('AdminProcesses')

    def _projects_parser(self, downloaded: BytesIO) -> Dict[int, List[str]]:
        self._logger.info('Start projects parser')
        file = BytesIO()
        file.write(downloaded.getvalue())
        file.seek(0)
        text = file.read().decode('utf-8')
        soup = BeautifulSoup(text, 'lxml')
        projects = [project for project in soup.find_all('li', class_='project-item')]
        data = {}
        for project in projects:
            courses = map(int, project.get('data-cursus').translate(str.maketrans('', '', '[ ]')).split(','))
            cursus_ids = filter(lambda cursus_id: cursus_id in self._config.courses, courses)
            for cursus_id in cursus_ids:
                project_name = project.find('a').text.strip()
                data.setdefault(cursus_id, []).append(project_name)
                self._logger.info('Extract project | %s | %s', cursus_id, project_name)
        self._logger.info('Parsing completed')
        return data

    async def projects_cursus_saver(self, message: Message) -> str:
        downloaded = await bot.download_file_by_id(message.document.file_id)
        try:
            data = self._projects_parser(downloaded=downloaded)
        except Exception as e:
            self._logger.error('Unknown projects parser error | %s ', e)
            return hcode(str(e))
        if not data:
            return 'Информация не обновлена, ничего не удалось спарсить'
        for cursus_id in data:
            project_ids = []
            self._logger.info('Get projects from cursus | %s | %s ', cursus_id, data[cursus_id])
            projects = await self._config.intra.get_projects(cursus_id=cursus_id, project_names=data[cursus_id])
            for project in projects:
                await Project.create_project(project_id=project['id'], name=project['name'], cursus_id=cursus_id)
                project_ids.append(project['id'])
                self._logger.info('Save project | %s | %s | %s', cursus_id, project['id'], project['name'])
            await Project.delete_projects_from_cursus(cursus_id=cursus_id, project_ids=project_ids)
            self._logger.info('Delete projects from cursus | %s | %s ', cursus_id, data[cursus_id])
        return 'Готово!'

    async def mailing(self, message: Union[str, Message], user: User, peer_id: int):
        try:
            if isinstance(message, Message):
                await message.copy_to(chat_id=user.id, reply_markup=menu_keyboard(user.language))
            else:
                await bot.send_message(chat_id=user.id, text=message)
            self._logger.info('Successful message sending | %s [%s] | completed', user.id, user.username)
            await asyncio.sleep(0.1)

        except (BotBlocked, UserDeactivated) as e:
            self._logger.error('Failed message sending | %s [%s] | %s | user deleted',
                               user.id, user.username, e)
            keys = [
                f'Peer.get_peer:{peer_id}',
                f'UserPeer._get_relationships:{user.id}',
                f'User.get_user_data:{user.id}',
                f'User.get_user_from_peer:{peer_id}'
            ]
            await user.delete()
            [await Cache().delete(key=key) for key in keys]

        except ChatNotFound as e:
            self._logger.error('Failed message sending | %s [%s] | %s | pass',
                               user.id, user.username, e)

    async def sending_messages(self, message: Message):
        offset = 0
        query = db.select([User, Peer]).select_from(User.outerjoin(Peer)).limit(100).offset(offset).order_by(User.id)
        result = await query.gino.load((User, Peer.id)).all()
        while result:
            self._logger.info('Start mailing for offset=%s', offset)
            for user, peer_id in result:
                await self.mailing(message=message, user=user, peer_id=peer_id)
            offset += 100
            query = db.select([User, Peer]).select_from(
                User.outerjoin(Peer)).limit(100).offset(offset).order_by(User.id)
            result = await query.gino.load((User, Peer.id)).all()
        self._logger.info('Completed mailing')
