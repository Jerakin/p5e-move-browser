import json
from pathlib import Path
from dataclasses import dataclass


@dataclass
class MoveFilter:
    name: str
    type: str
    power: str
    duration: str
    time: str
    pp: str
    range: str
    attack_type: str
    sort: str


def convert_move(name, _json):
    move = {}
    _range = _json["Range"]
    move["name"] = name
    move["description"] = _json["Description"]
    move["duration"] = _json["Duration"]
    move["power"] = _json["Move Power"] if "Move Power" in _json else None
    move["pp"] = str(_json["PP"])
    move["time"] = _json["Move Time"].title()
    move["range"] = "Self" if "Self" in _range else _range
    move["type"] = _json["Type"]
    if "Self" in _range:
        at = "melee"
    elif "Melee" in _range:
        at = "melee"
    elif "Varies" in _range:
        at = "melee/range"
    else:
        at = "range"
    move["attack_type"] = at
    return move


def _ok(v):
    return v and not v == 'None'


class MoveModel:
    def __init__(self):
        self.data = []
        self.load()

    def load(self):
        for move in (Path(__file__).parent / "p5e-data/data/moves").iterdir():
            with move.open("r") as fp:
                data = json.load(fp)
            mv = convert_move(move.stem, data)
            self.data.append(mv)

    def filter(self, filters):
        selected = []
        for move in self.data:
            if _ok(filters.name) and filters.name not in move["name"]:
                continue
            if _ok(filters.type) and not filters.type.lower() == move["type"].lower():
                continue
            if _ok(filters.power) and (move["power"] is not None and filters.power not in move["power"]) or move["power"] is None:
                continue
            if _ok(filters.range) and not filters.range == move["range"]:
                continue
            if _ok(filters.pp) and not filters.pp == move["pp"]:
                continue
            if _ok(filters.time) and not filters.time == move["time"]:
                continue
            if _ok(filters.attack_type) and filters.attack_type.lower() not in move["attack_type"]:
                continue
            selected.append(move)
        reverse = True if filters.sort[0] == '-' else False
        sort = filters.sort[1:] if reverse else filters.sort

        return sorted(selected, key=lambda d: d[sort], reverse=reverse)
