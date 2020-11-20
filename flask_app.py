import os

from flask import Flask, render_template, request, abort, jsonify, session
from flask_wtf import FlaskForm
from wtforms import StringField, TextField, SubmitField, SelectField, BooleanField
import wtforms.validators as validators
from werkzeug.datastructures import MultiDict

try:
    from . import model
except ImportError:
    import model

app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

move_model = model.MoveModel()

pokemon_model = model.PokemonMoveModel()
pokemon_model.move_model = move_model


def get_filter():
    filters = model.MoveFilter(
        request.args.get('species', default=None),
        request.args.get('variant', default=None),
        request.args.get('egg', default=None),
        request.args.get('tm', default=None),
        request.args.get('level', default=None),
        request.args.get('start', default=None),
        request.args.get('name', default=None),
        request.args.get('type', default=None),
        request.args.get('power', default=None),
        request.args.get('duration', default=None),
        request.args.get('time', default=None),
        request.args.get('pp', default=None),
        request.args.get('range', default=None),
        request.args.get('attack_type', default=None),
        request.args.get('save', default=None),
        request.args.get('concentration', default=None),
        request.args.get('sort', default='name')
    )

    return filters


def post_filter():
    filters = model.MoveFilter(
        request.form.get('species', default=None),
        request.form.get('variant', default=None),
        request.form.get('egg', default=None),
        request.form.get('tm', default=None),
        request.form.get('level', default=None),
        request.form.get('start', default=None),
        request.form.get('name', default=None),
        request.form.get('type', default=None),
        request.form.get('power', default=None),
        request.args.get('duration', default=None),
        request.args.get('time', default=None),
        request.form.get('pp', default=None),
        request.args.get('range', default=None),
        request.form.get('attack_type', default=None),
        request.form.get('save', default=None),
        request.form.get('concentration', default=None),
        request.args.get('sort', default='name')
    )

    return filters


def handle_session_data(filters):
    form_data = session.get('movefilterdata', None)
    if form_data and not request.args.get('filter', default=True) == "clear":
        form = SearchForm(MultiDict(form_data))
        filters.species = form.species.data
        filters.variant = form.variant.data
        filters.egg = form.egg.data
        filters.tm = form.tm.data
        filters.level = form.level.data
        filters.start = form.start.data
        filters.name = form.name.data
        filters.type = form.type.data
        filters.power = form.power.data
        filters.pp = form.pp.data
        filters.save = form.save.data
        filters.concentration = form.concentration.data
        filters.attack_type = form.attack_type.data


def get_request(objects, this_url="/"):
    form = SearchForm()
    sort = request.args.get('sort')
    reverse = not (sort and sort[0] == "-")
    return render_template("home.html", list=objects, form=form, sort=sort, reverse=reverse, this_url=this_url)


def post_request(objects, this_url="/"):
    form = SearchForm()
    session['movefilterdata'] = request.form
    return render_template("home.html", list=objects, form=form, this_url=this_url)


@app.route("/pokemon/<string:pokemon>", methods=['GET'])
def get_pokemon_list(pokemon):
    filters = get_filter()
    handle_session_data(filters)
    all_objects = pokemon_model.load(pokemon)
    objects = pokemon_model.filter(all_objects, filters)
    return get_request(objects, request.path)


@app.route("/pokemon/<string:pokemon>", methods=['POST'])
def post_pokemon_list(pokemon):
    filters = post_filter()
    all_objects = pokemon_model.load(pokemon)
    objects = pokemon_model.filter(all_objects, filters)
    return get_request(objects, request.path)


@app.route("/", methods=['GET'])
def get_moves_list():
    filters = get_filter()
    handle_session_data(filters)
    if filters.species:
        moves = pokemon_model.load(filters.species)
        objects = pokemon_model.filter(moves, filters)
    else:
        objects = move_model.filter(move_model.data, filters)
    return get_request(objects)


@app.route("/", methods=['POST'])
def post_moves_list():
    filters = post_filter()
    if filters.species:
        moves = pokemon_model.load(filters.species)
        objects = pokemon_model.filter(moves, filters)
    else:
        objects = move_model.filter(move_model.data, filters)
    return post_request(objects)


attributes = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']
pp = ['1', '3', '5', '10', '15', '20']
types = ["Normal", "Fire", "Water", "Electric", "Grass", "Ice", "Fighting", "Poison", "Ground", "Flying", "Psychic",
         "Bug", "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy"]

save_required = ([(None, ''), ('STR', "Strength"), ('DEX', "Dexterity"), ('CON', "Constitution"),
                  ('INT', "Intelligence"), ('WIS', "Wisdom"), ('CHA', "Charisma")])


def _fields(_list):
    t = [(x, x) for x in _list]
    t.insert(0, (None, ''))
    return t


class SearchForm(FlaskForm):
    species = StringField("Species")
    variant = SelectField(u'Variant', choices=[], default=None)
    start = BooleanField(u'Start', default=True)
    level = BooleanField(u'Level', default=True)
    tm = BooleanField(u'TM', default=True)
    egg = BooleanField(u'Egg', default=True)

    name = StringField('Name')
    attack_type = SelectField(u'Attack Type', choices=_fields(['Melee', 'Range']), default=None)
    power = SelectField(u'Move Power', choices=_fields(attributes), default=None)
    pp_field = _fields(pp)
    pp_field.append(('∞', "Unlimited"))
    pp = SelectField(u'PP', choices=pp_field, default=None)
    type = SelectField(u'Types', choices=_fields(types), default=None)
    save = SelectField(u'Save Required', choices=save_required, default=None)
    concentration = SelectField(u'Concentration Required', choices=[(None, ""), (True, "Yes")], default=None)
    filter = SubmitField('Filter Moves')
