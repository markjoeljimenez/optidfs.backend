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

def transformPlayers(players):
    playerList = []
    players = list(filter(lambda player: player["draftStatAttributes"][0]["value"] not in ['-'], players))

    for player in players:
        fppg = player["draftStatAttributes"][0]["value"]
        is_injured = True if player["status"] == "O" else False

        playerList.append(Player(
            player["playerId"],
            player["firstName"],
            player["lastName"],
            player["position"].split('/'),
            player["teamAbbreviation"],
            float(player["salary"]),
            0 if re.search('[a-zA-Z]', fppg) else float(fppg),
            is_injured,
            player["status"] if player["status"] != "O" else None,
            # False
        ))

    return playerList

@app.route('/')
def get_contests():
    return jsonpickle.encode(contests(sport=SportAPI.NBA))

@app.route('/players')
def get_players():
    global draftables

    draftId = request.args.get('id')
    response = requests.get('https://api.draftkings.com/draftgroups/v1/draftgroups/%s/draftables?format=json' % (draftId))
    draftables = response.json()["draftables"]

    return json.dumps(draftables)

@app.route('/optimize', methods=['GET', 'POST'])
def optimize():
    global draftables

    lockedPlayers = request.json["locked"]
   
    players = transformPlayers(draftables)
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
                player.is_locked = True
                optimizer.add_player_to_lineup(player)
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
