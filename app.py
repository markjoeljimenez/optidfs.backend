import json
import re
import requests
import jsonpickle
from flask import Flask, request
from flask_restful import Api, Resource, reqparse
from flask_cors import CORS
from pydfs_lineup_optimizer import get_optimizer, Site, Sport, Player, LineupOptimizerException, JSONLineupExporter
from pydfs_lineup_optimizer.constants import PlayerRank
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
        player["position"].split("/"),
        player["team"],
        player["salary"],
        player["points_per_contest"],
        True if player["status"] == "O" else False,
        PlayerRank.REGULAR,
        None,
        player["min_exposure"] if "min_exposure" in player else None,
        player["projected_ownership"] if "projected_ownership" in player else None
    )

    return player


@app.route("/")
def get_contests():
    return jsonpickle.encode(contests(sport=SportAPI.NBA))


@app.route("/players")
def get_players():
    # Get players
    draftables = available_players(request.args.get("id"))

    awayTeams = [team["away_team_id"]
                 for team in draftables["team_series_list"]]

    homeTeams = [team["home_team_id"]
                 for team in draftables["team_series_list"]]

    teams = [awayTeams, homeTeams]

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
        } for player in draftables["players"]],
        "teamIds": [y for x in teams for y in x]
    })


@app.route("/optimize", methods=["GET", "POST"])
def optimize():
    optimizer = get_optimizer(Site.DRAFTKINGS, Sport.BASKETBALL)

    json = request.get_json()

    generations = json.get('generations')
    lockedPlayers = json.get('lockedPlayers')
    players = json.get('players')
    rules = json.get('rules')

    optimizer.load_players([transform_player(player) for player in players])

    # optimizer.load_players_from_csv("DKSalaries-july29.csv")

    response = {
        "success": True,
        "message": None
    }

    if "NUMBER_OF_PLAYERS_FROM_SAME_TEAM" in rules:
        for team in rules['NUMBER_OF_PLAYERS_FROM_SAME_TEAM']:
            optimizer.set_players_from_one_team({
                team['key']: team['value']
            })

    if "NUMBER_OF_SPECIFIC_POSITIONS" in rules:
        for position in rules['NUMBER_OF_SPECIFIC_POSITIONS']:
            optimizer.set_players_with_same_position({
                position['key']: position['value']
            })

    if "MINIMUM_SALARY_CAP" in rules:
        optimizer.set_min_salary_cap(rules["MINIMUM_SALARY_CAP"])

    if "MAX_REPEATING_PLAYERS" in rules:
        optimizer.set_max_repeating_players(
            rules["MAX_REPEATING_PLAYERS"])

    if "PROJECTED_OWNERSHIP" in rules:
        optimizer.set_projected_ownership(
            min_projected_ownership=rules["PROJECTED_OWNERSHIP"])

    if lockedPlayers is not None:
        for player in lockedPlayers:
            optimizer.add_player_to_lineup(optimizer.get_player_by_id(player))

    try:
        optimize = optimizer.optimize(generations)
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
