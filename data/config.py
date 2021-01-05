from os import path

from services.utils import read_json


config = read_json(path.join('data', 'data.json'))
api_token = config['api_token']
clients = config['clients']
mongo_username = config['mongo_username']
mongo_password = config['mongo_password']
localization_texts = read_json(path.join('data', 'localization.json'))
