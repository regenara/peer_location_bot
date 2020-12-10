from os import path

from services.utils import read_json


config = read_json(path.join('data', 'data.json'))
api_token = config['api_token']
client_id = config['client_id']
client_secret = config['client_secret']
mongo_username = config['mongo_username']
mongo_password = config['mongo_password']
stalker_client_secret = config['stalker_client_secret']
stalker_client_id = config['stalker_client_id']
localization_texts = read_json(path.join('data', "localization.json"))

