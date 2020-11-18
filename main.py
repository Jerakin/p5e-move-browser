import os

from flask import Flask, render_template, request, abort, jsonify, session
from flask_wtf import FlaskForm
from wtforms import StringField, TextField, SubmitField, SelectField
import wtforms.validators as validators
from werkzeug.datastructures import MultiDict

try:
    from . import model
except ImportError:
    import model

app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

app_model = model.PokemonModel()
move_model = model.MoveModel()


@app.route("/")
def welcome():
    return render_template("welcome.html")


@app.route("/pokemon/<string:species>")
def show_pokemon(species):
    pkmn = app_model.get_pokemon_data(species)
    if not pkmn:
        abort(404)
    return render_template("pokemon.html", species=species, pokemon=pkmn)


@app.route("/pokemon/list")
def show_pokemon_list():
    filters = model.POKEMON_FILTER(
        request.args.get('gen', default=None),
        request.args.get('type', default=None),
        request.args.get('sr', default=None),
        request.args.get('level', default=None)
    )
    pokemon_list = app_model.get_pokemon_list(filters)
    return render_template("list.html", list=pokemon_list)


@app.route("/api/moves/list")
def api_moves_list():
    filters = model.MoveFilter(
        request.args.get('name', default=None),
        request.args.get('type', default=None),
        request.args.get('power', default=None),
        request.args.get('duration', default=None),
        request.args.get('time', default=None),
        request.args.get('pp', default=None),
        request.args.get('range', default=None),
        request.args.get('attack_type', default=None),
        request.args.get('sort', default='name')
    )
    return jsonify(move_model.filter(filters))


@app.route("/moves/list", methods=['GET'])
def get_moves_list():
    form = SearchForm()
    filters = model.MoveFilter(
        request.args.get('name', default=None),
        request.args.get('type', default=None),
        request.args.get('power', default=None),
        request.args.get('duration', default=None),
        request.args.get('time', default=None),
        request.args.get('pp', default=None),
        request.args.get('range', default=None),
        request.args.get('attack_type', default=None),
        request.args.get('sort', default='name')
    )

    formdata = session.get('filterdata', None)
    if formdata:
        form = SearchForm(MultiDict(formdata))
        filters.name = form.name.data
        filters.type = form.type.data
        filters.power = form.power.data
        filters.pp = form.pp.data
        filters.attack_type = form.attack_type.data

    objects = move_model.filter(filters)

    sort = request.args.get('sort')
    reverse = not (sort and sort[0] == "-")
    return render_template("move_list.html", list=objects, form=form, sort=sort, reverse=reverse)


@app.route("/moves/list", methods=['POST'])
def post_moves_list():
    form = SearchForm()
    filters = model.MoveFilter(
        request.form.get('name', default=None),
        request.form.get('type', default=None),
        request.form.get('power', default=None),
        request.args.get('duration', default=None),
        request.args.get('time', default=None),
        request.form.get('pp', default=None),
        request.args.get('range', default=None),
        request.form.get('attack_type', default=None),
        request.args.get('sort', default='name')
    )
    session['filterdata'] = request.form
    objects = move_model.filter(filters)
    return render_template("move_list.html", list=objects, form=form)


def _fields(_list):
    t = [(x, x) for x in _list]
    t.insert(0, (None, ''))
    return t

attributes = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']
pp = ['1', '3', '5', '10', '15', '20', 'Unlimited']
types = ["Normal", "Fire", "Water", "Electric", "Grass", "Ice", "Fighting", "Poison", "Ground", "Flying", "Psychic",
         "Bug", "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy"]


class SearchForm(FlaskForm):
    name = StringField('Name', [validators.optional()])
    attack_type = SelectField(u'Attack Type', choices=_fields(['Melee', 'Range']), default=None)
    power = SelectField(u'Attack Power', choices=_fields(attributes), default=None)
    pp = SelectField(u'PP', choices=_fields(pp), default=None)
    type = SelectField(u'Types', choices=_fields(types), default=None)

    filter = SubmitField('Filter')
