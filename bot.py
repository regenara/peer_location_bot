from aiogram import executor

from misc import dp
from services import filters

for custom_filter in (filters.IsIntrovert, filters.IsExtrovert, filters.IsStart,
                      filters.IsHelp, filters.IsAbout, filters.IsDonate,
                      filters.IsRemoveFriend, filters.IsMailing,
                      filters.IsLocations, filters.IsProjects):
    dp.filters_factory.bind(custom_filter)


import handlers

if __name__ == '__main__':
    executor.start_polling(dp)
