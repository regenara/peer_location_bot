from aiogram.utils.helper import Helper
from aiogram.utils.helper import HelperMode
from aiogram.utils.helper import Item


class States(Helper):
    mode = HelperMode.snake_case

    MAILING = Item()
    AUTH = Item()
    THROTTLER = Item()
