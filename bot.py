from aiogram import Bot, Dispatcher, executor, types

import intra_auth
from utils import read_json

api_token = read_json('data.json')['api_token']
bot = Bot(token=api_token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer('Привет! Пришли мне ник пользователя и я скажу где он сидит. Можно прислать сразу несколько '
                         'ников через запятую (не более 5)')


@dp.message_handler()
async def echo(message: types.Message):
    nicknames = message.text.strip().lower().replace('@', '').replace(' ', '').split(',')
    texts = []
    alone = True
    if len(nicknames) > 1:
        alone = False
    for nickname in nicknames[:5]:
        nickname = nickname.strip()
        token = intra_auth.get_token()
        get_info = intra_auth.get_user(nickname, token)
        text = f'Пользователь <b>{nickname}</b> не найден! Проверь правильность введенных данных'
        if get_info:
            displayname = get_info['displayname']
            login = get_info['login']
            cursus_users = get_info['cursus_users']
            cursus_info = '\n'.join([f'<b>{c["cursus"]["name"]}:</b> {round(c["level"], 2)}' for c in cursus_users])
            campus = get_info['campus'][0]['name']
            image_url = get_info['image_url']
            location = get_info['location']
            if location is None:
                location = 'Не в кампусе'
            if get_info['staff?'] and location is None:
                location = 'Спроси в АДМ'
            text = f'<b>{displayname}</b> aka {login}\n{cursus_info}\n<b>Кампус:</b> {campus}\n<b>Место:</b> {location}'
            if alone:
                text += f'<a href="{image_url}">​</a>'
        texts.append(text)
    await message.answer(f'\n➖➖➖➖➖➖➖➖➖➖\n'.join(texts))


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
