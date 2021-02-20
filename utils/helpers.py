from datetime import datetime
from pytz import timezone
from typing import List
from typing import Tuple

from aiogram.types import InlineKeyboardMarkup
from aiogram.types.inline_keyboard import InlineKeyboardButton

from misc import intra_requests
from services.keyboards import pagination_keyboard
from services.keyboards import peer_keyboard


def keyboard_normalize(buttons: List[List[InlineKeyboardButton]], friends: List[str],
                       notifications: List[str]) -> InlineKeyboardMarkup:
    peers = [button.callback_data.split('=')[1] for row in buttons for button in row][::2]
    is_host_message = False
    if buttons[-1][0].callback_data.split('=')[0] == 'host':
        peers = [button.callback_data.split('=')[1] for row in buttons for button in row][:2:2]
        is_host_message = True
    keyboard = peer_keyboard(peers, friends, notifications)
    if is_host_message:
        host, page, campus = buttons[-1][-1].callback_data.split('=')[1:]
        keyboard = pagination_keyboard('host', 1, host, 0, 3, int(page) - 1, keyboard, campus)
    return keyboard


def friends_list_normalization(message_text: str, friends: list) -> str:
    friends_data = message_text.split('\n\n')
    friends_list = [s for s in friends_data[1:] if any(x in s for x in friends)]
    new_friends_list = []
    for data in friends_list:
        strings = []
        lines = data.splitlines()
        if len(lines) > 1:
            for i, string in enumerate(lines):
                if not i:
                    strings.append(f'<b>{string[:string.index("aka")]}</b>'
                                   f'aka <code>{string[string.index("aka") + 4:]}</code>')
                else:
                    strings.append(f'<b>{string[:string.index(":") + 1]}</b>{string[string.index(":") + 1:]}')
        else:
            string = lines[0]
            strings.append(f'<b>{string[:string.index(":") + 1]}</b>{string[string.index(":") + 1:]}')
        new_friends_list.append('\n'.join(strings))
    if new_friends_list:
        new_friends_list.insert(0, f'<b>{friends_data[0]}</b>')
    else:
        return ''
    return '\n\n'.join(new_friends_list)


def nickname_valid(nickname: str) -> bool:
    return 1 < len(nickname) < 20 and not any(n in './\\#% \n?!' for n in nickname)


async def nicknames_separation(nicknames: list) -> Tuple[List[str], List[str]]:
    bad_nicknames = []
    nicknames_copy = nicknames.copy()
    for nickname in nicknames_copy:
        if not nickname_valid(nickname):
            nicknames.remove(nickname)
            if len(nickname) > 20:
                nickname = f'{nickname[:20]}...'
            bad_nicknames.append(nickname)
    bad_nicknames = list(dict.fromkeys(bad_nicknames))
    if len(nicknames) < 2:
        return nicknames, bad_nicknames
    peers = await intra_requests.get_peers(nicknames)
    if isinstance(peers, list):
        peer_nicknames = [peer['login'] for peer in peers]
    else:
        return nicknames, bad_nicknames
    for nickname in nicknames:
        if nickname not in peer_nicknames:
            bad_nicknames.append(nickname)
    peer_nicknames.reverse()
    return peer_nicknames, bad_nicknames


def get_utc(iso_format: str) -> float:
    if iso_format:
        return datetime.fromisoformat(iso_format.replace('Z', '+00:00')).timestamp()
    return .0


def get_str_time(iso_format: str, time_zone: str) -> str:
    if iso_format:
        time_format = '%H:%M  %d.%m.%y'
        return datetime.fromisoformat(iso_format.replace('Z', '+00:00')).\
            astimezone(timezone(time_zone)).strftime(time_format)
    return ''


def get_log_time(begin_at: str, end_at: str, now: str) -> str:
    log_time = f'{begin_at} - {end_at or now}'
    if begin_at[7:] == end_at[7:]:
        log_time = f'{begin_at[:5]} - {end_at[:5]}  {begin_at[7:]}'
    return log_time


def get_peer_title(status: str, link: str, full_name: str, nickname: str) -> str:
    return f'{status}<u><a href="{link}">{full_name}</a></u> aka <code>{nickname}</code>\n'


def get_data_from_message(message_text: str) -> Tuple[str, str, str, str]:
    raws = message_text.splitlines()[0].split()
    full_name = ' '.join(raws[1:-2])
    nickname = raws[-1]
    status = f'{raws[0]} '
    link = f'https://profile.intra.42.fr/users/{nickname}'
    return status, link, full_name, nickname
