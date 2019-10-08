import json
import re
import requests
import jsonpickle
from flask import Flask, request
from flask_restful import Api, Resource, reqparse
from flask_cors import CORS
from pydfs_lineup_optimizer import get_optimizer, Site, Sport, Player, JSONLineupExporter, LineupOptimizerException
from draft_kings.data import Sport as SportAPI
from draft_kings.client import contests

app = Flask(__name__)
CORS(app, support_credentials=True)
api = Api(app)

def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z

def transformPlayers(players):
    players = list(filter(lambda player: player["draftStatAttributes"][0]["value"] not in ['-'], players))

    playerList = []

    for player in players:
        fppg = player["draftStatAttributes"][0]["value"]

        playerList.append(Player(
            player["playerId"],
            player["firstName"],
            player["lastName"],
            [ player["position"] ],
            player["teamAbbreviation"],
            float(player["salary"]),
            0 if re.search('[a-zA-Z]', fppg) else float(fppg)
        ))


    return playerList

@app.route('/')
def get_contests():
    return jsonpickle.encode(contests(sport=SportAPI.NBA))

@app.route('/optimize')
def optimize():
    draftId = request.args.get('id')

    response = requests.get('https://api.draftkings.com/draftgroups/v1/draftgroups/%s/draftables?format=json' % (draftId))

    players = transformPlayers(response.json()["draftables"])

    optimizer = get_optimizer(Site.DRAFTKINGS, Sport.BASKETBALL)
    optimizer.load_players(players)

    optimize = optimizer.optimize(1)

    success = {
        "success": True,
        "message": None
    }

    try:
        exporter = JSONLineupExporter(optimize)

        exportedJSON = exporter.export()

        return merge_two_dicts(exportedJSON, success)
    except LineupOptimizerException as exception:
        success["success"] = False
        success["message"] = exception.message

        return success
