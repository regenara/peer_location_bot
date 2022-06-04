from typing import (List,
                    Tuple,
                    Union)
from urllib.parse import urlencode

from aiogram.types import (InlineKeyboardButton,
                           InlineKeyboardMarkup,
                           KeyboardButton,
                           ReplyKeyboardMarkup)
from aiogram.utils.parts import paginate

from config import Config
from db_models.campuses import Campus
from db_models.peers import Peer as PeerDB
from db_models.projects import Project
from db_models.users import User
from models.peer import Peer


def auth_keyboard(message_id: int, user_id: int, language_code: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(resize_keyboard=True)
    state = Config.fernet.encrypt(f'{message_id}.{user_id}.{language_code}'.encode('utf-8'))
    query = urlencode({'client_id': Config.application.client_id, 'redirect_uri': Config.bot_base_url,
                       'response_type': 'code', 'scope': 'public', 'state': state})
    keyboard.add(InlineKeyboardButton(Config.local.auth.get(language_code),
                                      url=f'https://api.intra.42.fr/oauth/authorize?{query}'))
    return keyboard


def donate_keyboard(language: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(resize_keyboard=True)
    keyboard.add(InlineKeyboardButton(Config.local.donate_link.get(language), url='https://donate.stream/jakebv'))
    return keyboard


def menu_keyboard(language: str) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    buttons = [KeyboardButton(text) for text in Config.local.menu.get(language).values()]
    keyboard.row(*buttons[:2])
    keyboard.row(*buttons[2:4])
    keyboard.row(*buttons[4:])
    return keyboard


def settings_keyboard(user: User) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    statuses = {True: ('✅', 'no'), False: ('❌', 'yes')}
    texts = (Config.local.avatar.get, Config.local.default_campus.get, Config.local.notify.get,
             Config.local.peer_left.get, Config.local.anon.get)
    callbacks = ('avatar', 'campus', 'notify', 'left_peer', 'telegram')
    settings = (user.show_avatar, user.use_default_campus, user.notify, user.left_peer, user.show_me)
    buttons = [InlineKeyboardButton(Config.local.language.get(user.language),
                                    callback_data=Config.local.languages.get(user.language))]
    for text, callback, setting in zip(texts, callbacks, settings):
        status = statuses[setting][0]
        callback_data = f'{statuses[setting][1]}_{callback}'
        buttons.append(InlineKeyboardButton(text=text(user.language, status=status), callback_data=callback_data))
    if not user.username:
        buttons.pop(-1)
    keyboard.add(*buttons)
    return keyboard


def courses_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    for cursus_id, cursus in Config.courses.items():
        keyboard.insert(InlineKeyboardButton(cursus, callback_data=f'courses.{cursus_id}'))
    return keyboard


def peer_keyboard(peers: List[Peer], friends: List[PeerDB], observables: List[PeerDB],
                  payload: str = '') -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    friends_list = [friend.login for friend in friends]
    observables_list = [observable.login for observable in observables]
    friend_statuses = {True: ('✅', 'remove'), False: ('❌', 'add')}
    observable_statuses = {True: ('🔔', 'off'), False: ('🔕', 'on')}
    for peer in peers:
        friend_status = friend_statuses[peer.login in friends_list]
        observable_status = observable_statuses[peer.login in observables_list]
        friend_text = f'{peer.login} {friend_status[0]}'
        friend_callback_data = f'{friend_status[1]}.{peer.id}.{peer.login}.{payload}'
        observable_text = f'{peer.login} {observable_status[0]}'
        observable_callback_data = f'{observable_status[1]}.{peer.id}.{peer.login}.{payload}'
        keyboard.row(InlineKeyboardButton(friend_text, callback_data=friend_callback_data),
                     InlineKeyboardButton(observable_text, callback_data=observable_callback_data))
    return keyboard


def alone_peer_keyboard(user: User, login: str, keyboard: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    for k, v in Config.local.alone_peer_menu.get(user.language).items():
        keyboard.insert(InlineKeyboardButton(text=v, callback_data=f'{k}.{login}'))
    return keyboard


def pagination_keyboard(action: str, count: int, content: Union[str, int], limit: int, stop: int,
                        page: int = 0, keyboard: InlineKeyboardMarkup = None,
                        back_button_data: Tuple[str, str] = None) -> InlineKeyboardMarkup:
    keyboard = keyboard or InlineKeyboardMarkup(row_width=3)
    pages = {
        1: '1️⃣', 2: '2️⃣', 3: '3️⃣', 4: '4️⃣', 5: '5️⃣',
        6: '6️⃣', 7: '7️⃣', 8: '8️⃣', 9: '9️⃣', 10: '🔟'
    }
    buttons = []
    back_button = None
    if back_button_data:
        back_button = InlineKeyboardButton(back_button_data[0], callback_data=back_button_data[1])
    if count > limit:
        if not page:
            if back_button:
                buttons.append(back_button)
            buttons.append(InlineKeyboardButton(f'{pages[page + 2]}➡️', callback_data=f'{action}.{content}.1'))
        elif page == stop:
            buttons.append(InlineKeyboardButton(f'⬅️{pages[page]}', callback_data=f'{action}.{content}.{stop - 1}'))
            if back_button:
                buttons.append(back_button)
        else:
            buttons.append(InlineKeyboardButton(f'⬅️{pages[page]}', callback_data=f'{action}.{content}.{page - 1}'))
            if back_button:
                buttons.append(back_button)
            buttons.append(InlineKeyboardButton(f'{pages[page + 2]}➡️', callback_data=f'{action}.{content}.{page + 1}'))
    elif count <= limit and page:
        buttons.append(InlineKeyboardButton(f'⬅️{pages[page]}', callback_data=f'{action}.{content}.{page - 1}'))
        if back_button:
            buttons.append(back_button)
    elif back_button:
        buttons.append(back_button)
    keyboard.row(*buttons)
    return keyboard


def data_keyboard(data: Union[List[Project], List[Campus]], action: str, content: Union[str, int], limit: int,
                  current_id: int = 0, page: int = 0, back_button_data: Tuple[str, str] = None) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=3)
    count = len(data[page * limit:])
    data = paginate(data=data, page=page, limit=limit)
    for entity in data:
        text = entity.name if current_id != entity.id else f'✅ {entity.name}'
        callback_data = f'{action}.{content}.{entity.id}.{page}'
        keyboard.insert(InlineKeyboardButton(text, callback_data=callback_data))
    keyboard = pagination_keyboard(action=f'{action}_pagination', count=count, content=content, limit=limit,
                                   stop=9, page=page, keyboard=keyboard, back_button_data=back_button_data)
    return keyboard


def keyboard_normalize(friends: List[PeerDB], observables: List[PeerDB],
                       buttons: List[List[InlineKeyboardButton]], payload: str) -> InlineKeyboardMarkup:
    if payload == 'pagination':
        peers_data = [button.callback_data.split('.')[1:3] for row in buttons for button in row][:-2:2]
    elif payload == 'alone_peer':
        peers_data = [button.callback_data.split('.')[1:3] for row in buttons for button in row][:2:2]
    else:
        peers_data = [button.callback_data.split('.')[1:3] for row in buttons for button in row][::2]
    peers = []
    for peer in peers_data:
        peers.append(Peer(id=int(peer[0]), login=peer[1]))
    keyboard = peer_keyboard(peers=peers, friends=friends, observables=observables, payload=payload)
    if payload == 'pagination':
        pagination_buttons = buttons[-1:][0]
        keyboard.row(*pagination_buttons)
    elif payload == 'alone_peer':
        alone_peer_buttons = buttons[1:]
        [keyboard.row(*buttons) for buttons in alone_peer_buttons]
    return keyboard
