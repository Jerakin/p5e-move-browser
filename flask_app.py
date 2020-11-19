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
    pokemon_filters = model.PokemonFilter(
        request.args.get('species', default=None),
        request.args.get('variant', default=None),
        request.args.get('egg', default=None),
        request.args.get('tm', default=None),
        request.args.get('level', default=None),
        request.args.get('start', default=None)
    )

    return filters, pokemon_filters


def post_filter():
    filters = model.MoveFilter(
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

    pokemon_filters = model.PokemonFilter(
        request.form.get('species', default=None),
        request.form.get('variant', default=None),
        request.form.get('egg', default=None),
        request.form.get('tm', default=None),
        request.form.get('level', default=None),
        request.form.get('start', default=None)
    )
    return filters, pokemon_filters


def handle_session_data(filters, pokemon_filters):
    pokemon_form_data = session.get('pokemonfilterdata', None)
    form_data = session.get('movefilterdata', None)
    if form_data and not request.args.get('filter', default=True) == "clear":
        form = SearchForm(MultiDict(form_data))
        filters.name = form.name.data
        filters.type = form.type.data
        filters.power = form.power.data
        filters.pp = form.pp.data
        filters.save = form.save.data
        filters.concentration = form.concentration.data
        filters.attack_type = form.attack_type.data

    if pokemon_form_data and not request.args.get('filter', default=True) == "clear":
        form = PokemonSearchForm(MultiDict(form_data))
        pokemon_filters.species = form.species.data
        pokemon_filters.variant = form.variant.data
        pokemon_filters.start = form.start.data
        pokemon_filters.level = form.level.data
        pokemon_filters.tm = form.tm.data
        pokemon_filters.egg = form.egg.data


def get_request(objects, this_url="/"):
    form = SearchForm()
    pokemon_form = PokemonSearchForm()
    sort = request.args.get('sort')
    reverse = not (sort and sort[0] == "-")
    return render_template("move_list.html", list=objects, pokemon_form=pokemon_form, form=form, sort=sort, reverse=reverse, this_url=this_url)


def post_request(objects, this_url="/"):
    form = SearchForm()
    pokemon_form = PokemonSearchForm()
    session['movefilterdata'] = request.form
    session['pokemonfilterdata'] = pokemon_form.form
    return render_template("move_list.html", list=objects, pokemon_form=pokemon_form, form=form, this_url=this_url)


@app.route("/pokemon/<string:pokemon>", methods=['GET'])
def get_pokemon_list(pokemon):
    filters, pkmn_filters = get_filter()
    handle_session_data(filters, pkmn_filters)
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
    filters, pkmn_filters = get_filter()
    handle_session_data(filters, pkmn_filters)
    objects = move_model.filter(move_model.data, filters)
    return get_request(objects)


@app.route("/", methods=['POST'])
def post_moves_list():
    filters = post_filter()
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
    name = StringField('Name', [validators.optional()])
    attack_type = SelectField(u'Attack Type', choices=_fields(['Melee', 'Range']), default=None)
    power = SelectField(u'Move Power', choices=_fields(attributes), default=None)
    pp_field = _fields(pp)
    pp_field.append(('∞', "Unlimited"))
    pp = SelectField(u'PP', choices=pp_field, default=None)
    type = SelectField(u'Types', choices=_fields(types), default=None)
    save = SelectField(u'Save Required', choices=save_required, default=None)
    concentration = SelectField(u'Concentration Required', choices=[(None, ""), (True, "Yes")], default=None)
    filter = SubmitField('Filter Moves')


class PokemonSearchForm(FlaskForm):
    species = StringField("Species", [validators.optional()])
    variant = SelectField(u'Move Power', choices=[], default=None)
    start = BooleanField(u'Start', default=False)
    level = BooleanField(u'Level', default=False)
    tm = BooleanField(u'TM', default=False)
    egg = BooleanField(u'Egg', default=False)
