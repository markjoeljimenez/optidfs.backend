from os import environ
import csv
import io
import json
import re
import requests
import jsonpickle
import pydash
import pandas as pd
from flask import Flask, request, session, Response
from flask_restful import Api, Resource, reqparse
from flask_cors import CORS
from pydfs_lineup_optimizer import get_optimizer, Site, Sport, Player, LineupOptimizerException, JSONLineupExporter, TeamStack, PositionsStack, PlayersGroup, Stack
from draft_kings.data import SPORT_ID_TO_SPORT
from draft_kings.client import contests, available_players, draftables, draft_group_details, sports
from utils import SPORT_ID_TO_PYDFS_SPORT, transform_player, merge_two_dicts, generate_csv, get_positions, generate_csv_from_csv

application = Flask(__name__)
application.debug = True
application.config["SECRET_KEY"] = environ.get("SECRET_KEY")
# application.config["SESSION_TYPE"] = "filesystem"
application.config["SESSION_COOKIE_HTTPONLY"] = False
application.config["SESSION_COOKIE_SAMESITE"] = None

CORS(application, supports_credentials=True)


@application.route("/")
def get_sports():
    response = list(map(
        (lambda sport: {**sport, "supported": sport["sportId"] in SPORT_ID_TO_PYDFS_SPORT}), sports()["sports"]))

    return json.dumps(response)


@application.route("/contests", methods=["GET", "POST"])
def get_contests():
    json = request.get_json()

    if json:
        sport = json.get("sport")

        if sport:
            return jsonpickle.encode(contests(sport=SPORT_ID_TO_SPORT[sport]))

    return {}


@application.route("/players", methods=["GET", "POST"])
def get_players():
    # json = request.get_json()

    # if request.args.get("id"):
    #     # Get players
    #     players = available_players(request.args.get("id"))["players"]

    #     return json.dumps({
    #         "players": [{
    #             "id": player["id"],
    #             # "draftable_id": player["draftable_id"],
    #             "first_name": player["first_name"],
    #             "last_name": player["last_name"],
    #             "position": player["position"]["name"],
    #             "team": player["team"],
    #             "salary": player["draft"]["salary"],
    #             "points_per_contest": player["points_per_contest"],
    #             "status": player["status"]
    #         } for player in players]
    #         # "teamIds": [y for x in teams for y in x]
    #     })

    try:
        if request.files:
            df = pd.read_csv(request.files.get("csv"))

            return json.dumps({
                "players": [{
                    "id": player["ID"],
                    # "draftable_id": player["draftable_id"],
                    "first_name": player["Name"].split()[0],
                    "last_name": player["Name"].split()[1] if len(player["Name"].split()) > 1 else "",
                    "position": player["Position"],
                    "team": player["TeamAbbrev"],
                    "salary": player["Salary"],
                    "points_per_contest": player["AvgPointsPerGame"],
                    "draft_positions": player["Roster Position"]
                    # "status": player["status"]
                } for index, player in df.iterrows()]
            })
    except:
        return Response(
            "Unable to get players",
            status=400,
        )


@application.route("/optimize", methods=["GET", "POST"])
def optimize():
    json = request.get_json()

    lockedPlayers = json.get("lockedPlayers")
    players = json.get("players")
    rules = json.get("rules")
    session["sport"] = SPORT_ID_TO_PYDFS_SPORT[json.get("sport")]
    session["draftGroupId"] = json.get("draftGroupId")

    optimizer = get_optimizer(
        Site.DRAFTKINGS, session.get("sport")["sport"])
    optimizer.load_players([transform_player(player)
                            for player in players])
    # optimizer.load_players_from_csv("DKSalaries-nfl-sept-5.csv")

    response = {
        "success": True,
        "message": None
    }

    if "NUMBER_OF_PLAYERS_FROM_SAME_TEAM" in rules:
        for team in rules["NUMBER_OF_PLAYERS_FROM_SAME_TEAM"]:
            optimizer.set_players_from_one_team({
                team["key"]: team["value"]
            })

    if "NUMBER_OF_SPECIFIC_POSITIONS" in rules:
        for position in rules["NUMBER_OF_SPECIFIC_POSITIONS"]:
            optimizer.set_players_with_same_position({
                position["key"]: position["value"]
            })

    if "MINIMUM_SALARY_CAP" in rules:
        optimizer.set_min_salary_cap(rules["MINIMUM_SALARY_CAP"])

    if "MAX_REPEATING_PLAYERS" in rules:
        optimizer.set_max_repeating_players(
            rules["MAX_REPEATING_PLAYERS"])

    if "MAX_PROJECTED_OWNERSHIP" in rules or "MIN_PROJECTED_OWNERSHIP" in rules:
        optimizer.set_projected_ownership(
            min_projected_ownership=rules["MIN_PROJECTED_OWNERSHIP"] if "MIN_PROJECTED_OWNERSHIP" in rules else None, max_projected_ownership=rules["MAX_PROJECTED_OWNERSHIP"] if "MAX_PROJECTED_OWNERSHIP" in rules else None)

    if lockedPlayers is not None:
        for player in lockedPlayers:
            optimizer.add_player_to_lineup(optimizer.get_player_by_id(player))

    try:
        optimize = optimizer.optimize(rules["NUMBER_OF_GENERATIONS"])

        exporter = JSONLineupExporter(optimize)
        exported_json = exporter.export()

        session["lineups"] = exported_json["lineups"]

        # csv_exporter = DraftKingsCSVLineupExporter(optimize)
        # csv_exporter.export("result.csv", lambda player: player.id)

        return merge_two_dicts(exported_json, response)
    except LineupOptimizerException as exception:
        return Response(
            exception.message,
            status=400,
        )


@application.route("/export")
def exportCSV():
    if "lineups" in session:
        lineups = session.get("lineups")
        # draftGroupId = session.get("draftGroupId")
        sport = session.get("sport")

        # csv = generate_csv(lineups, draftGroupId, sport)
        csv = generate_csv_from_csv(lineups, sport)

        # response = make_response(csv)
        # response.headers["Content-Disposition"] = "attachment; filename=DKSalaries.csv"
        # response.headers["Content-type"] = "text/csv"

        return Response(csv,
                        mimetype="text/csv",
                        headers={"Content-disposition":
                                 "attachment; filename=DKSalaries.csv"})

    return {}
