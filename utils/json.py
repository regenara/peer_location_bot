import json
from typing import Union


def read_json(json_file: str) -> Union[dict, list]:
    with open(json_file) as f:
        data = json.load(f)
    return data


def write_json(data: dict or list, json_file: str):
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)
