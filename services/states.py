from aiogram.utils.helper import (Helper,
                                  HelperMode,
                                  Item)


class States(Helper):
    mode = HelperMode.snake_case

    MAILING = Item()
    UPDATE_PROJECTS = Item()

    AUTH = Item()
    GRANTED = Item()
    THROTTLER = Item()
