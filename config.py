from utils import read_json


config = read_json('data.json')
api_token = config['api_token']
client_id = config['client_id']
client_secret = config['client_secret']
mongo_username = config['mongo_username']
mongo_password = config['mongo_password']
localization_texts = read_json("localization.json")
