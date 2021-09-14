import asyncio

from aiogram.types import Message
from aiogram.utils.exceptions import (BotBlocked,
                                      ChatNotFound,
                                      UserDeactivated)

from bot import dp
from config import Config
from db_models import db
from db_models.peers import Peer
from db_models.projects import Project
from db_models.users import User
from misc import bot
from services.keyboards import menu_keyboard
from services.states import States
from utils.cache import Cache
from utils.helpers import projects_parser


@dp.message_handler(state='mailing', content_types='any')
async def mailing(message: Message):
    await dp.current_state(user=message.from_user.id).set_state(States.GRANTED)
    if message.text == '$':
        await message.answer('Отменено')
    else:
        await message.answer('Рассылка началась')
        offset = 0
        query = db.select([User, Peer]).select_from(User.outerjoin(Peer)).limit(100).offset(offset).order_by(User.id)
        result = await query.gino.load((User, Peer.id)).all()
        while result:
            for user, peer_id in result:
                try:
                    await message.copy_to(chat_id=user.id, reply_markup=menu_keyboard(user.language))
                    await asyncio.sleep(0.1)
                except (BotBlocked, UserDeactivated):
                    keys = [
                        f'Peer.get_peer:{peer_id}',
                        f'UserPeer._get_relationships:{user.id}',
                        f'User.get_user_data:{user.id}',
                        f'User.get_user_from_peer:{peer_id}'
                    ]
                    if user.username:
                        keys.append(f'User.get_login_from_username:{user.username.lower()}')
                    await user.delete()
                    [await Cache().delete(key=key) for key in keys]
                except ChatNotFound:
                    pass
            offset += 100
            query = db.select([User, Peer]).select_from(
                User.outerjoin(Peer)).limit(100).offset(offset).order_by(User.id)
            result = await query.gino.load((User, Peer.id)).all()
        await message.answer('Готово!')


@dp.message_handler(is_mailing=True, state='*')
async def before_mailing(message: Message):
    await dp.current_state(user=Config.admin).set_state(States.MAILING)
    await message.answer("Пришли сообщение, которое надо разослать, или отправь $ для отмены")


@dp.message_handler(state='update_projects', content_types=['document', 'text'])
async def update_projects(message: Message):
    await dp.current_state(user=message.from_user.id).set_state(States.GRANTED)
    if message.content_type == 'text':
        await message.answer('Отменено')
    else:
        await message.answer('Обновление началась. Это может занять несколько минут')
        downloaded = await bot.download_file_by_id(message.document.file_id)
        data = projects_parser(downloaded=downloaded)
        for cursus_id in data:
            project_ids = []
            projects = await Config.intra.get_projects(cursus_id=cursus_id, project_names=data[cursus_id])
            for project in projects:
                await Project.create_project(project_id=project['id'], name=project['name'], cursus_id=cursus_id)
                project_ids.append(project['id'])
            await Project.delete_projects_from_cursus(cursus_id=cursus_id, project_ids=project_ids)
        await message.answer('Готово!')


@dp.message_handler(is_update_projects=True, state='*')
async def before_update_projects(message: Message):
    await dp.current_state(user=Config.admin).set_state(States.UPDATE_PROJECTS)
    await message.answer('Пришли html файл со <a href="https://projects.intra.42.fr/projects/list">страницы</a> '
                         'или отправь любой текст для отмены')
