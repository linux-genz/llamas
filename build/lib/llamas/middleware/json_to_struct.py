#/usr/lib/python3
from collections import namedtuple
import json
import os

from pdb import set_trace


# class MsgTemplate:

#     def __init__(self, *args, **kwargs):
#         pass


def read_json(path):
    if not os.path.exists(path):
        return None

    result = None
    with open(path, 'r') as file_obj:
        result = file_obj.read()

    return json.loads(result)


def get_props(data):
    nla_map = []
    for key in data.keys():
        entry = data[key]
        if isinstance(entry[1], str):
            nla_map.append(tuple(entry))
        elif isinstance(entry[1], dict):
            for prop_name in entry:
                props = get_props(entry[1])
                nla_map.append((
                    entry[0],
                    { key : props }
                ))
    return tuple(nla_map)


def build_object(data, props, model_name):
    struct_msg = namedtuple(model_name, 'nla_map')
    nla_map = props
    for prop in props:
        if isinstance(prop[1], dict):
            set_trace()
    return None


def generate_model(json_path):
    data = read_json(json_path)
    # struct_msg = namedtuple('MsgModel', 'nla_map')
    for key in data.keys():
        props = get_props(data[key])
        msg = build_object(data[key], props, 'MsgModel')
    set_trace()
    return data