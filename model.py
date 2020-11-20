import json
import sys
from pathlib import Path
from dataclasses import dataclass
import copy

tm_lookup = {
  "1": "Work Up",
  "2": "Dragon Claw",
  "3": "Psyshock",
  "4": "Calm Mind",
  "5": "Roar",
  "6": "Toxic",
  "7": "Hail",
  "8": "Bulk Up",
  "9": "Venoshock",
  "10": "Hidden Power",
  "11": "Sunny Day",
  "12": "Taunt",
  "13": "Ice Beam",
  "14": "Blizzard",
  "15": "Hyper Beam",
  "16": "Light Screen",
  "17": "Protect",
  "18": "Rain Dance",
  "19": "Roost",
  "20": "Safeguard",
  "21": "Frustration",
  "22": "Solar Beam",
  "23": "Smack Down",
  "24": "Thunderbolt",
  "25": "Thunder",
  "26": "Earthquake",
  "27": "Return",
  "28": "Leech Life",
  "29": "Psychic",
  "30": "Shadow Ball",
  "31": "Brick Break",
  "32": "Double Team",
  "33": "Reflect",
  "34": "Sludge Wave",
  "35": "Flamethrower",
  "36": "Sludge Bomb",
  "37": "Sandstorm",
  "38": "Fire Blast",
  "39": "Rock Tomb",
  "40": "Aerial Ace",
  "41": "Torment",
  "42": "Facade",
  "43": "Flame Charge",
  "44": "Rest",
  "45": "Attract",
  "46": "Thief",
  "47": "Low Sweep",
  "48": "Round",
  "49": "Echoed Voice",
  "50": "Overheat",
  "51": "Steel Wing",
  "52": "Focus Blast",
  "53": "Energy Ball",
  "54": "False Swipe",
  "55": "Scald",
  "56": "Fling",
  "57": "Charge Beam",
  "58": "Sky Drop",
  "59": "Brutal Swing",
  "60": "Quash",
  "61": "Will-O-Wisp",
  "62": "Acrobatics",
  "63": "Embargo",
  "64": "Explosion",
  "65": "Shadow Claw",
  "66": "Payback",
  "67": "Smart Strike",
  "68": "Giga Impact",
  "69": "Rock Polish",
  "70": "Aurora Veil",
  "71": "Stone Edge",
  "72": "Volt Switch",
  "73": "Thunder Wave",
  "74": "Gyro Ball",
  "75": "Swords Dance",
  "76": "Fly",
  "77": "Psych Up",
  "78": "Bulldoze",
  "79": "Frost Breath",
  "80": "Rock Slide",
  "81": "X-Scissor",
  "82": "Dragon Tail",
  "83": "Infestation",
  "84": "Poison Jab",
  "85": "Dream Eater",
  "86": "Grass Knot",
  "87": "Swagger",
  "88": "Sleep Talk",
  "89": "U-Turn",
  "90": "Substitute",
  "91": "Flash Cannon",
  "92": "Trick Room",
  "93": "Wild Charge",
  "94": "Surf",
  "95": "Snarl",
  "96": "Nature Power",
  "97": "Dark Pulse",
  "98": "Waterfall",
  "99": "Dazzling Gleam",
  "100": "Confide"
}


@dataclass
class MoveFilter:
    species: str
    variant: str
    egg: bool
    tm: bool
    level: bool
    start: bool
    name: str
    type: str
    power: str
    duration: str
    time: str
    pp: str
    range: str
    attack_type: str
    save: str
    concentration: str
    sort: str


def convert_move(name, _json):
    move = {}
    _range = _json["Range"]
    move["name"] = name
    move["description"] = _json["Description"]
    move["duration"] = _json["Duration"].replace(", Concentration", "")
    move["power"] = _json["Move Power"] if "Move Power" in _json else None
    pp = str(_json["PP"])
    if "Unl" in pp:
        pp = '∞'
    move["pp"] = pp
    move["time"] = _json["Move Time"].title()
    move["range"] = "Self" if "Self" in _range else _range
    move["type"] = _json["Type"]
    move["concentration"] = True if "Concentration" in _json["Duration"] else False
    if "Self" in _range:
        at = "melee"
    elif "Melee" in _range:
        at = "melee"
    elif "Varies" in _range:
        at = "melee/range"
    else:
        at = "range"
    move["attack_type"] = at
    move["save"] = _json["Save"] if "Save" in _json else None
    return move


def _ok(v):
    return v and not v == 'None'


class PokemonMoveModel:
    def __init__(self):
        self.data = {}
        self.evolve_from = {}
        self.move_model: MoveModel = None
        self.list = []
        self.__build_list()
        self.__cache_evolve_from_data()

    def __build_list(self):
        for pkmn in (Path(__file__).parent / "p5e-data/data/pokemon").iterdir():
            self.list.append(pkmn.stem)

    def __cache_evolve_from_data(self):
        with (Path(__file__).parent / "p5e-data/data/evolve.json").open("r") as fp:
            evolve_data = json.load(fp)
        for species, data in evolve_data.items():
            if "into" in data:
                for into in data["into"]:
                    self.evolve_from[into] = species

    def __collect_moves(self, species, data):
        moves = {"TM": [], "Starting Move": [], "Egg": []}
        for level in data["Moves"]["Level"]:
            for name in data["Moves"]["Level"][level]:
                if f"Level {level}" not in moves:
                    moves[f"Level {level}"] = []
                moves[f"Level {level}"].append(name)

        moves["Starting Move"] = data["Moves"]["Starting Moves"]

        if "egg" in data["Moves"]:
            moves["Egg"] = data["Moves"]["egg"]
        else:
            evolved_from = species
            while evolved_from:
                evolved_from = self.evolve_from[evolved_from] if evolved_from in self.evolve_from else False
                if evolved_from:
                    cached_moves = self.load(evolved_from)
                    for move in cached_moves:
                        if move["source"] == "Egg":
                            name = move["name"]
                            if name not in moves["Egg"]:
                                moves["Egg"].append(move["name"])

        for n in data["Moves"]["TM"]:
            moves["TM"].append(tm_lookup[str(n)])
        return moves

    def add_move(self, move, source):
        index = self.move_model.lookup[move]
        move = copy.deepcopy(self.move_model.data[index])
        move["source"] = source
        return move

    def filter(self, data, filters):
        selected = []
        for move in data:
            if filters.tm is None and move["source"] == "TM":
                continue
            if filters.level is None and "Level" in move["source"]:
                continue
            if filters.start is None and "Start" in move["source"]:
                continue
            if filters.egg is None and move["source"] == "Egg":
                continue

            selected.append(move)
        return self.move_model.filter(selected, filters)

    def load(self, pokemon):
        pokemon = pokemon.title()
        if pokemon in self.data:
            return self.data[pokemon]
        data_file = (Path(__file__).parent / "p5e-data/data/pokemon" / (pokemon + '.json'))
        if data_file.exists():
            with data_file.open("r") as fp:
                data = json.load(fp)
            moves = self.__collect_moves(pokemon, data)
            self.data[pokemon] = []
            for source, moves in moves.items():
                for move in moves:
                    self.data[pokemon].append(self.add_move(move, source))

            return self.data[pokemon]
        else:
            print("Could not find", data_file, file=sys.stderr)
        return []


class MoveModel:
    def __init__(self):
        self.data = []
        self.lookup = {}
        self.load()

    def load(self):
        for index, move in enumerate((Path(__file__).parent / "p5e-data/data/moves").iterdir()):
            with move.open("r") as fp:
                data = json.load(fp)
            mv = convert_move(move.stem, data)
            self.lookup[move.stem] = index
            self.data.append(mv)

    def filter(self, data, filters):
        selected = []
        for move in data:
            if _ok(filters.name) and filters.name.lower() not in move["name"].lower():
                continue
            if _ok(filters.type) and not filters.type.lower() == move["type"].lower():
                continue
            if _ok(filters.power) and (filters.power not in move["power"]):
                continue
            if _ok(filters.range) and not filters.range == move["range"]:
                continue
            if _ok(filters.pp) and not filters.pp == move["pp"]:
                continue
            if _ok(filters.time) and not filters.time == move["time"]:
                continue
            if _ok(filters.attack_type) and filters.attack_type.lower() not in move["attack_type"]:
                continue
            if _ok(filters.save) and not filters.save == move["save"]:
                continue
            if _ok(filters.concentration) and not move["concentration"]:
                continue

            selected.append(move)
        reverse = True if filters.sort[0] == '-' else False
        sort = filters.sort[1:] if reverse else filters.sort

        return sorted(selected, key=lambda d: d[sort], reverse=reverse)


if __name__ == '__main__':
    mm = MoveModel()
    pmm = PokemonMoveModel()
    pmm.move_model = mm
    print("-- Abomasnow")
    pmm.load("Abomasnow")
    print("-- Abra")
    pmm.load("Abra")
