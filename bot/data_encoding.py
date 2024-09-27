import json


def encode_data(data):
    if isinstance(data, str):
        return data
    return json.dumps(data)

def decode_data(data):
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return data