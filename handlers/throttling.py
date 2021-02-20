from data.config import LOCALIZATION_TEXTS
from misc import mongo
from models.user import User


async def throttled(*args, **kwargs):
    message = args[0]
    user_id = message.from_user.id
    data = await mongo.find('users', {'user_id': user_id})
    user = User.from_dict(data)
    rate = kwargs['rate']
    text = LOCALIZATION_TEXTS['antiflood'][user.lang].format(rate=rate)
    await message.reply(text)
