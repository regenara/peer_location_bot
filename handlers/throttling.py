from data.config import localization_texts
from misc import mongo


async def throttled(*args, **kwargs):
    message = args[0]
    user_id = message.from_user.id
    lang = await mongo.get_lang(user_id)
    rate = kwargs['rate']
    text = eval(localization_texts['antiflood'][lang])
    await message.reply(text)
