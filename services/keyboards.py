from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton


def language_keyboard() -> InlineKeyboardMarkup:
    language_kb = InlineKeyboardMarkup(row_width=2)
    language_kb.row(InlineKeyboardButton('Русский 🇷🇺', callback_data='ru'),
                    InlineKeyboardButton('English 🇬🇧', callback_data='en'))
    return language_kb


def avatar_keyboard(yes: str, no: str) -> InlineKeyboardMarkup:
    avatar_kb = InlineKeyboardMarkup(row_width=2)
    avatar_kb.row(InlineKeyboardButton(f'{yes} ✅', callback_data='yes'),
                  InlineKeyboardButton(f'{no} ❌', callback_data='no'))
    return avatar_kb


def results_count_keyboard() -> InlineKeyboardMarkup:
    results_kb = InlineKeyboardMarkup(row_width=4)
    for n in (5, 15, 30, 50):
        results_kb.insert(InlineKeyboardButton(f'{n}', callback_data=f'{n}'))
    return results_kb


def intra_users_keyboard(intra_users: list, friends: list, notifications: list) -> InlineKeyboardMarkup:
    intra_users_kb = InlineKeyboardMarkup(row_width=2)
    for intra_user in intra_users:
        is_friend = '❌'
        alert = '🔕'
        friend = 'addToSet'
        switch_alert = 'on'
        if intra_user in friends:
            is_friend = '✅'
            friend = 'pull'
        if intra_user in notifications:
            alert = '🔔'
            switch_alert = 'off'
        intra_users_kb.row(InlineKeyboardButton(f'{intra_user} {is_friend}', callback_data=f'{friend}={intra_user}'),
                           InlineKeyboardButton(f'{intra_user} {alert}', callback_data=f'{switch_alert}={intra_user}'))
    return intra_users_kb
