"""import asyncio

import intra_requests
from bot import bot
from utils import read_json, write_json


async def check_user():
    users = read_json('data.json')['users']
    token = intra_requests.get_token()
    for user in users:
        get_info = intra_requests.get_user(user, token)
        location = get_info['location']
        get_data = read_json('stalking.json')
        data = get_data.get(user)
        if data is None:
            data = {'location': location}
        if location is None:
            get_data.update({user: {'location': None}})
        elif location != data['location']:
            await bot.send_message(, f'{user} в кампусе!\n{location}')
            get_data.update({user: {'location': location}})
        write_json(get_data, 'stalking.json')


if __name__ == '__main__':
    asyncio.run(check_user())
"""