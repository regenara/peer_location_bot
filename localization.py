from utils import read_json


get_texts = read_json("localization.json")


def get_user_info(lang: str = 'en') -> dict:
    user_info = get_texts['user_info'][lang]
    return user_info
