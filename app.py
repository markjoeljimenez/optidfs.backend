import json
import re
import requests
import jsonpickle
import pydash
from flask import Flask, request
from flask_restful import Api, Resource, reqparse
from flask_cors import CORS
from pydfs_lineup_optimizer import get_optimizer, Site, Sport, Player, LineupOptimizerException, DraftKingsCSVLineupExporter, JSONLineupExporter
from pydfs_lineup_optimizer.constants import PlayerRank
from draft_kings.data import Sport as SportAPI
from draft_kings.client import contests, available_players, draftables, draft_group_details
from nba_api.stats.static import players
from nba_api.stats.endpoints import commonplayerinfo, playerprofilev2
from utils import transform_player, merge_two_dicts, get_sport

app = Flask(__name__)
app.debug = True
CORS(app, support_credentials=True)
api = Api(app)


@app.route("/", methods=["GET", "POST"])
def get_contests():
    json = request.get_json()

    sport = json.get('sport')

    return jsonpickle.encode(contests(sport=SportAPI[sport]))


@app.route("/players")
def get_players():
    id = request.args.get("id")

    def get_draftable_id(player):
        return pydash.find(draftables(
            id)["draftables"], lambda _player: _player["id"] == player["id"])["draftable_id"]

    # Get players
    players = available_players(id)["players"]

    def map_player(id, player):
        return {
            **player,
            "id": id
        }

    transformed_players = map(map_player, [get_draftable_id(player)
                                           for player in players], players)

    return json.dumps({
        "players": [{
            "id": player["id"],
            # "draftable_id": player["draftable_id"],
            "first_name": player["first_name"],
            "last_name": player["last_name"],
            "position": player["position"]["name"],
            "team": player["team"],
            "salary": player["draft"]["salary"],
            "points_per_contest": player["points_per_contest"],
            "status": player["status"]
        } for player in transformed_players]
        # "teamIds": [y for x in teams for y in x]
    })


@ app.route("/optimize", methods=["GET", "POST"])
def optimize():
    json = request.get_json()

    generations = json.get('generations')
    lockedPlayers = json.get('lockedPlayers')
    players = json.get('players')
    rules = json.get('rules')
    sport = json.get('sport')

    optimizer = get_optimizer(Site.DRAFTKINGS, get_sport(sport))

    optimizer.load_players([transform_player(player) for player in players])
    # optimizer.load_players_from_csv("DKSalaries-nfl-sept-5.csv")

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
        # exportedJSON = exporter.export()

        # csv_exporter = DraftKingsCSVLineupExporter(optimize)
        # csv_exporter.export(
        #     'result.csv', lambda player: player.id)

        return merge_two_dicts(exporter.export(), response)
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
