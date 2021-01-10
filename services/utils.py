import json


def read_json(json_file: str) -> dict or list:
    with open(json_file) as f:
        data = json.load(f)
    return data


def write_json(data: dict or list, json_file: str):
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)


def nickname_check(nickname: str) -> bool:
    return 1 < len(nickname) < 20 and not any(c in './\\#% \n?!' for c in nickname)


def safe_split_text(text: str) -> list:
    temp_text = text
    parts = []
    length = 3500
    while temp_text:
        if len(temp_text) > length:
            try:
                split_pos = temp_text[:length].rindex(f'\n{"—" * 10}')
            except ValueError:
                split_pos = length
            if split_pos < length // 4 * 3:
                split_pos = length
            parts.append(temp_text[:split_pos])
            temp_text = temp_text[split_pos:].lstrip()
        else:
            parts.append(temp_text)
            break
    return parts
