from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton


def language_keyboard() -> InlineKeyboardMarkup:
    language_kb = InlineKeyboardMarkup(row_width=2)
    language_kb.row(InlineKeyboardButton('Русский 🇷🇺', callback_data='ru'),
                    InlineKeyboardButton('English 🇬🇧', callback_data='en'))
    return language_kb


def avatar_keyboard(yes: str, no: str) -> InlineKeyboardMarkup:
    language_kb = InlineKeyboardMarkup(row_width=2)
    language_kb.row(InlineKeyboardButton(f'{yes} ✅', callback_data='yes'),
                    InlineKeyboardButton(f'{no} ❌', callback_data='no'))
    return language_kb


def intra_users_keyboard(intra_users: list, friends: dict) -> InlineKeyboardMarkup:
    intra_users_kb = InlineKeyboardMarkup(row_width=2)
    for intra_user in intra_users:
        is_friend = '✅'
        notification = '🔔'
        switch = 'on'
        if friends.get(intra_user) is not None:
            is_friend = '❌'
            if friends['notification']:
                notification = '🔕'
                switch = 'off'
        intra_users_kb.row(InlineKeyboardButton(f'{intra_user} {is_friend}', callback_data=intra_user),
                           InlineKeyboardButton(f'{intra_user} {notification}', callback_data=f'{switch}={intra_user}'))
    return intra_users_kb

