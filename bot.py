from aiogram import Bot, Dispatcher, executor, types

from text_generator import text_compile
from utils import read_json

api_token = read_json('data.json')['api_token']
bot = Bot(token=api_token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer('Привет! Пришли мне ник пользователя и я скажу где он сидит. Можно прислать сразу несколько '
                         'ников через пробел (не более 5)')


@dp.message_handler()
async def echo(message: types.Message):
    text = text_compile(message.text, 'en', True)
    await message.answer(text)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
