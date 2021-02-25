from typing import List
from typing import Union
from urllib.parse import urlencode
import base64

from aiogram.types import InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import KeyboardButton
from aiogram.types import ReplyKeyboardMarkup

from data.config import CLIENT_ID
from data.config import LOCALIZATION_TEXTS
from data.config import REDIRECT_URI
from misc import mongo


page_nums = {1: '1️⃣', 2: '2️⃣', 3: '3️⃣', 4: '4️⃣', 5: '5️⃣',
             6: '6️⃣', 7: '7️⃣', 8: '8️⃣', 9: '9️⃣', 10: '🔟'}


def auth_keyboard(message_id: int, user_id: int, ) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(resize_keyboard=True)
    state = base64.b16encode(f'{message_id}-{user_id}'.encode('utf-8'))
    url = 'https://api.intra.42.fr/oauth/authorize'
    query = urlencode({'client_id': CLIENT_ID, 'redirect_uri': REDIRECT_URI,
                       'response_type': 'code', 'scope': 'public',
                       'state': state})
    keyboard.add(InlineKeyboardButton('Authorization\nАвторизация', url=f'{url}?{query}'))
    return keyboard


def menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    texts = LOCALIZATION_TEXTS['menu'][lang]
    buttons = []
    for text in list(texts)[1:]:
        buttons.append(KeyboardButton(f'{texts[text]}'))
    keyboard.add(KeyboardButton(f'{texts["friends"]}')).add(*buttons)
    return keyboard


def language_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.row(InlineKeyboardButton('Русский 🇷🇺', callback_data='ru'),
                 InlineKeyboardButton('English 🇬🇧', callback_data='en'))
    return keyboard


def settings_keyboard(action: str, yes: str, no: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.row(InlineKeyboardButton(f'{yes} ✅', callback_data=f'yes_{action}'),
                 InlineKeyboardButton(f'{no} ❌', callback_data=f'no_{action}'))
    return keyboard


def peer_keyboard(peers: list, friends: List[str], notifications: List[str]) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    for nickname in peers:
        is_friend = '❌'
        alert = '🔕'
        friend = 'addToSet'
        switch_alert = 'on'
        if nickname in friends:
            is_friend = '✅'
            friend = 'pull'
        if nickname in notifications:
            alert = '🔔'
            switch_alert = 'off'
        keyboard.row(InlineKeyboardButton(f'{nickname} {is_friend}', callback_data=f'{friend}={nickname}'),
                     InlineKeyboardButton(f'{nickname} {alert}', callback_data=f'{switch_alert}={nickname}'))
    return keyboard


def pagination_keyboard(action: str, count: int, content: Union[str, int], results: int, stop: int, page: int = 0,
                        keyboard: InlineKeyboardMarkup = None, extra: str = None) -> InlineKeyboardMarkup:
    keyboard = keyboard or InlineKeyboardMarkup(row_width=2)
    extra_data = ''
    if extra:
        extra_data = f'={extra}'
    if count > results:
        if not page:
            keyboard.row(InlineKeyboardButton(f'{page_nums[page + 2]}➡️',
                                              callback_data=f'{action}={content}=1{extra_data}'))
        elif page == stop:
            keyboard.row(InlineKeyboardButton(f'⬅️{page_nums[page]}',
                                              callback_data=f'{action}={content}={stop - 1}{extra_data}'))
        else:
            keyboard.row(InlineKeyboardButton(f'⬅️{page_nums[page]}',
                                              callback_data=f'{action}={content}={page - 1}{extra_data}'),
                         InlineKeyboardButton(f'{page_nums[page + 2]}➡️',
                                              callback_data=f'{action}={content}={page + 1}{extra_data}'))
    elif count <= results and page:
        keyboard.row(InlineKeyboardButton(f'⬅️{page_nums[page]}',
                                          callback_data=f'{action}={content}={page - 1}{extra_data}'))
    return keyboard


async def projects_keyboard(page: int, results: int, project_id: int = 0) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=3)
    projects42 = await mongo.get_collections('projects42')
    collections = await projects42.to_list(length=130)
    collections.sort(key=lambda key: key['project_id'])
    projects = collections[page * 27:page * 27 + 27]
    count = len(projects)
    for project in projects:
        text = f'{project["name"]}'
        if project_id == project["project_id"]:
            text = f'📕 {project["name"]}'
        keyboard.insert(InlineKeyboardButton(text,
                                             callback_data=f'projects={project["project_id"]}={page}'))
    keyboard = pagination_keyboard('projects', count, 'projects', results, 4, page, keyboard, 'pagination')
    return keyboard
