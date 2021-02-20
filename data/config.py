from os import path

from utils.json import read_json


config = read_json(path.join('data', 'data2.json'))
API_TOKEN = config['api_token']
ADMIN = config['admin']
CLIENTS = config['clients']
CLIENT_ID = CLIENTS[0]['client_id']
CLIENTS_SECRET = CLIENTS[0]['client_secret']
REDIRECT_URI = config['redirect_uri']
MONGO_USERNAME = config['mongo_username']
MONGO_PASSWORD = config['mongo_password']
LOCALIZATION_TEXTS = read_json(path.join('data', 'localization.json'))
