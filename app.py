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
            False
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
   
    players = transformPlayers(draftables)
    optimizer = get_optimizer(Site.DRAFTKINGS, Sport.BASKETBALL)
    optimizer.load_players(players)

    if request.json["locked"] != None:
        player = optimizer.get_player_by_id(int(request.json["locked"]))
        player.is_locked = True
        print(player.is_locked)
        optimizer.add_player_to_lineup(player)

    success = {
        "success": True,
        "message": None
    }

    try:
        optimize = optimizer.optimize(1)
        # for lineup in optimize: 
        #     print(lineup)
        exporter = JSONLineupExporter(optimize)
        exportedJSON = exporter.export()
        return merge_two_dicts(exportedJSON, success)
    except LineupOptimizerException as exception:
        success["success"] = False
        success["message"] = exception.message
        return success
