import json
import re
import requests
import jsonpickle
from flask import Flask, request
from flask_restful import Api, Resource, reqparse
from flask_cors import CORS
from pydfs_lineup_optimizer import get_optimizer, Site, Sport, Player, LineupOptimizerException, JSONLineupExporter
from draft_kings.data import Sport as SportAPI
from draft_kings.client import contests, available_players, draftables, draft_group_details
from nba_api.stats.static import players
from nba_api.stats.endpoints import commonplayerinfo, playerprofilev2

app = Flask(__name__)
app.debug = True
CORS(app, support_credentials=True)
api = Api(app)


def merge_two_dicts(x, y):
    z = x.copy()   # start with x"s keys and values
    z.update(y)    # modifies z with y"s keys and values & returns None
    return z


def transform_player(player):
    player = Player(
        player["id"],
        player["first_name"],
        player["last_name"],
        player["position"]["name"].split("/"),
        player["team"],
        player["draft"]["salary"],
        player["points_per_contest"],
        True if player["status"] == "O" else False
        # 1,
        # None if player[7] is not "O" else player[7],
        # "Q"
        # False
    )

    return player


@app.route("/")
def get_contests():
    return jsonpickle.encode(contests(sport=SportAPI.NBA))


@app.route("/players")
def get_players():
    # Get players
    draftables = available_players(request.args.get("id"))

    return json.dumps({
        "players": [{
            "id": player["id"],
            "first_name": player["first_name"],
            "last_name": player["last_name"],
            "position": player["position"]["name"],
            "team": player["team"],
            "salary": player["draft"]["salary"],
            "points_per_contest": player["points_per_contest"],
            "status": player["status"]
        } for player in draftables["players"]]
    })


@app.route("/optimize", methods=["GET", "POST"])
def optimize():
    draftables = available_players(request.args.get("id"))

    optimizer = get_optimizer(Site.DRAFTKINGS, Sport.BASKETBALL)
    optimizer.load_players([transform_player(player)
                            for player in draftables["players"]])
    # optimizer.load_players_from_csv("DKSalaries-july29.csv")

    response = {
        "success": True,
        "message": None
    }

    try:
        optimize = optimizer.optimize(int(request.args.get(
            "n")))
        exporter = JSONLineupExporter(optimize)
        exportedJSON = exporter.export()

        return merge_two_dicts(exportedJSON, response)
    except LineupOptimizerException as exception:
        response["success"] = False
        response["message"] = exception.message
        return response


@ app.route("/stats")
def stats():
    playerId = players.find_players_by_full_name(
        request.args.get('player'))[0].get('id', None)

    player_info = json.loads(commonplayerinfo.CommonPlayerInfo(
        player_id=playerId).get_normalized_json()).get('CommonPlayerInfo', None)[0]
    player_headline_stats = json.loads(commonplayerinfo.CommonPlayerInfo(
        player_id=playerId).get_normalized_json()).get('PlayerHeadlineStats', None)[0]

    player_stats = json.loads(playerprofilev2.PlayerProfileV2(
        per_mode36="PerGame", player_id=playerId).get_normalized_json())

    teamId = player_info.get('TEAM_ID', None)

    profile_picture = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/%s/2019/260x190/%s.png" % (
        teamId, playerId)

    return {
        **player_info,
        **player_headline_stats,
        **player_stats,
        "profile_picture": profile_picture
    }
