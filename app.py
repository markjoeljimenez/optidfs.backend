import json
import re
import requests
import jsonpickle
from flask import Flask, request
from flask_restful import Api, Resource, reqparse
from flask_cors import CORS
from pydfs_lineup_optimizer import get_optimizer, Site, Sport, Player, JSONLineupExporter, LineupOptimizerException
from draft_kings.data import Sport as SportAPI
from draft_kings.client import contests, available_players, draftables, draft_group_details

app = Flask(__name__)
CORS(app, support_credentials=True)
api = Api(app)
draftables = None

def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z

def transform_player(player):
    is_injured = True if player["status"] == "O" else False

    player = Player(
        player["id"],
        player["first_name"],
        player["last_name"],
        player["position"]["name"].split('/'),
        player["team"],
        player["draft"]["salary"],
        player["points_per_contest"],
        is_injured,
        player["status"] if player["status"] != "O" else None,
        # False
    )

    return player

@app.route('/')
def get_contests():
    return jsonpickle.encode(contests(sport=SportAPI.NBA))

@app.route('/players')
def get_players():
    global draftables

    draftId = request.args.get('id')
    draftables = available_players(draftId)

    return draftables

@app.route('/optimize', methods=['GET', 'POST'])
def optimize():
    global draftables

    lockedPlayers = request.json["locked"]
    excludedPlayers = request.json["excluded"]

    players = [transform_player(player) for player in draftables["players"]]
    optimizer = get_optimizer(Site.DRAFTKINGS, Sport.BASKETBALL)
    optimizer.load_players(players)

    response = {
        "success": True,
        "message": None
    }

    if lockedPlayers != None:
        for lockedPlayer in lockedPlayers:
            try:
                player = optimizer.get_player_by_id(lockedPlayer)
                optimizer.add_player_to_lineup(player)
            except LineupOptimizerException as exception:
                response["success"] = False
                response["message"] = exception.message
                return response

    if excludedPlayers != None:
        for excludedPlayer in excludedPlayers:
            try:
                player = optimizer.get_player_by_id(excludedPlayer)
                optimizer.remove_player(player)
            except LineupOptimizerException as exception:
                response["success"] = False
                response["message"] = exception.message
                return response

    try:
        optimize = optimizer.optimize(1)
        exporter = JSONLineupExporter(optimize)
        exportedJSON = exporter.export()
        return merge_two_dicts(exportedJSON, response)
    except LineupOptimizerException as exception:
        response["success"] = False
        response["message"] = exception.message
        return response
