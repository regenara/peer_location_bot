from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton


def language_keyboard() -> InlineKeyboardMarkup:
    language_kb = InlineKeyboardMarkup(row_width=2)
    language_kb.row(InlineKeyboardButton('Русский 🇷🇺', callback_data='ru'),
                    InlineKeyboardButton('English 🇬🇧', callback_data='en'))
    return language_kb


def avatar_keyboard(yes: str, no: str) -> InlineKeyboardMarkup:
    language_kb = InlineKeyboardMarkup(row_width=2)
    language_kb.row(InlineKeyboardButton(f'{yes} ✅ ', callback_data='yes'),
                    InlineKeyboardButton(f'{no} ❌', callback_data='no'))
    return language_kb

