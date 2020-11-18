import json
import copy
from pathlib import Path
from collections import namedtuple
from dataclasses import dataclass

GENERATIONS = [[1, 151], [152, 251], [252, 386], [387, 493], [494, 649], [650, 721], [722, 809]]

POKEMON_FILTER = namedtuple("Filters", ["generations", "types", "sr", "level"])


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


pokemon_entry = {
    "species": "",
    "types": "",
    "size": "",
    "sr": "",
    "level": "",
    "egg": "",
    "gender": "",
    "evolution": "",
    "asi": "",
    "flavor": "",
    "ac": "",
    "hp": "",
    "hd": "",
    "speed": [],
    "attributes": {"STR": "", "DEX": "", "CON": "", "INT": "", "WIS": "", "CHA": ""},
    "skills": [],
    "saves": "",
    "senses": "",
    "abilities": [],
    "hidden": "",
    "index": []
}


def index_to_gen(index):
    for generation, (low, high) in enumerate(GENERATIONS):
        if int(index) < high:
            return generation + 1


def _filter_pokemon_list(data, filters):
    pokemon_list = []
    try:
        gen_filter = [int(x) for x in filters.generations.split(",")] if filters.generations else None
    except ValueError:
        gen_filter = None

    try:
        level_filter = int(filters.level) if filters.level else None
    except ValueError:
        level_filter = None

    type_filter = [x.lower() for x in filters.types.split(",")] if filters.types else None
    for species, pokemon in data.items():
        gen = index_to_gen(pokemon["index"])
        pokemon_type = [x.lower() for x in pokemon["Type"]]
        sr = pokemon["SR"]
        level = pokemon["MIN LVL FD"]

        if filters.generations and gen not in gen_filter:
            continue

        if type_filter:
            if len(pokemon_type) == 1 and not pokemon_type[0] in type_filter:
                continue
            else:
                if [True for filter_type in type_filter if filter_type not in pokemon_type]:
                    continue
        if level_filter and level > level_filter:
            continue

        if filters.sr and sr not in filters.sr:
            continue

        pokemon_list.append(species)
    return pokemon_list


def convert_pokemon(species, _json):
    pkmn = copy.deepcopy(pokemon_entry)
    pkmn["species"] = species
    pkmn["types"] = "/".join(_json["Type"])
    pkmn["size"] = pkmn["size"]
    pkmn["sr"] = "/".join([str(x) for x in _json["SR"].as_integer_ratio()])
    pkmn["level"] = _json["MIN LVL FD"]
    pkmn["egg"] = ""
    pkmn["gender"] = ""
    pkmn["evolution"] = ""
    pkmn["asi"] = ""
    pkmn["flavor"] = ""
    pkmn["ac"] = _json["AC"]
    pkmn["hp"] = _json["HP"]
    pkmn["hd"] = f'd{_json["Hit Dice"]}'
    pkmn["speed"] = ""
    pkmn["attributes"] = _json["attributes"]
    pkmn["skills"] = _json["Skill"]
    pkmn["saves"] = _json["saving_throws"]
    pkmn["senses"] = _json["Senses"]
    pkmn["abilities"] = _json["Abilities"]
    pkmn["hidden"] = _json["Hidden Ability"]
    pkmn["index"] = _json["index"]
    return pkmn


class PokemonModel:
    def __init__(self):
        self.filter_data = None
        self.pokemon_data = {}

    def get_pokemon_data(self, species):
        if species not in self.pokemon_data:
            path = Path(f"./p5e-data/data/pokemon/{species}.json")
            if not path.exists():
                return None
            with path.open("r") as fp:
                data = json.load(fp)
                self.pokemon_data[species] = convert_pokemon(species, data)

        return self.pokemon_data[species]

    def get_pokemon_list(self, filters):
        if not self.filter_data:
            with Path("./p5e-data/data/filter_data.json").open("r") as fp:
                self.filter_data = json.load(fp)
        return _filter_pokemon_list(self.filter_data, filters)


def convert_move(name, _json):
    move = copy.deepcopy(pokemon_entry)
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
        for move in Path(f"./p5e-data/data/moves").iterdir():
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
