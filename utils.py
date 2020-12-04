import json


def read_json(json_file):
    with open(json_file) as f:
        data = json.load(f)
    return data


def write_json(data, json_file):
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)