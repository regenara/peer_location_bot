from aiogram.types import Message

from bot import dp
from config import Config
from services.states import States
from utils.helpers import AdminProcesses


@dp.message_handler(state='mailing', content_types='any')
async def mailing(message: Message):
    await dp.current_state(user=message.from_user.id).set_state(States.GRANTED)
    if message.text == '$':
        await message.answer('Отменено')
    else:
        await message.answer('Рассылка началась')
        await AdminProcesses().sending_messages(message=message)
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
        text = await AdminProcesses().projects_cursus_saver(message=message)
        await message.answer(text)


@dp.message_handler(is_update_projects=True, state='*')
async def before_update_projects(message: Message):
    await dp.current_state(user=Config.admin).set_state(States.UPDATE_PROJECTS)
    await message.answer('Пришли html файл со <a href="https://projects.intra.42.fr/projects/list">страницы</a> '
                         'или отправь любой текст для отмены')
