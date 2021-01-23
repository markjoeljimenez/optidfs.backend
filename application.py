from datetime import datetime
from draft_kings.client import contests, sports
from draft_kings.data import SPORT_ID_TO_SPORT
from flask import Flask, request, session, Response, jsonify
from flask_cors import CORS
from os import environ
from pydfs_lineup_optimizer import get_optimizer, LineupOptimizerException, JSONLineupExporter
from utils import SPORT_ID_TO_PYDFS_SPORT, transform_player, generate_csv_from_csv, get_available_players, is_captain_mode
import csv
import json
import jsonpickle
import pandas as pd
import requests

application = Flask(__name__)
application.debug = True
application.config["SECRET_KEY"] = environ.get("SECRET_KEY")
application.config["SESSION_COOKIE_HTTPONLY"] = False
application.config["SESSION_COOKIE_SAMESITE"] = None

CORS(application, supports_credentials=True)

headers = {
    "Ocp-Apim-Subscription-Key": environ.get("FANTASY_DATA_KEY")
}


@application.route("/")
def get_sports():
    try:
        date = '2019-12-29'

        # response = list(map(
        #     (lambda sport: {**sport, "supported": sport["sportId"] in SPORT_ID_TO_PYDFS_SPORT}), sports()["sports"]))

        # return json.dumps(response)

        return jsonify(requests.get(
            f'{environ.get("FANTASY_DATA_ENDPOINT")}/{date}', headers=headers).json())
    except:
        return Response(
            "Unable to reach servers",
            status=500,
        )


@ application.route("/contests", methods=["GET", "POST"])
def get_contests():
    json = request.get_json()

    try:
        if json:
            sport = json.get("sport")

            if sport:
                return jsonpickle.encode(contests(sport=SPORT_ID_TO_SPORT[sport]))

    except:
        return Response(
            "Unable to get contests",
            status=500,
        )


@ application.route("/players", methods=["GET", "POST"])
def get_players():
    try:
        if request.args.get("id"):
            players = get_available_players(request.args.get("id"))

            return json.dumps({
                "players": [{
                    "id": player["ID"],
                    "first_name": player["Name"].split()[0],
                    "last_name": player["Name"].split()[1] if len(player["Name"].split()) > 1 else "",
                    "position": player["Position"],
                    "team": player["TeamAbbrev"],
                    "salary": player["Salary"],
                    "points_per_contest": player["AvgPointsPerGame"],
                    "draft_positions": player["Roster Position"]
                } for index, player in players.iterrows()]
            })

        if request.files:
            df = pd.read_csv(request.files.get("csv"))

            return json.dumps({
                "players": [{
                    "id": player["ID"],
                    "first_name": player["Name"].split()[0],
                    "last_name": player["Name"].split()[1] if len(player["Name"].split()) > 1 else "",
                    "position": player["Position"],
                    "team": player["TeamAbbrev"],
                    "salary": player["Salary"],
                    "points_per_contest": player["AvgPointsPerGame"],
                    "draft_positions": player["Roster Position"]
                } for index, player in df.iterrows()]
            })
    except:
        return Response(
            "Unable to get players",
            status=500,
        )


@application.route("/optimize", methods=["GET", "POST"])
def optimize():
    json = request.get_json()

    lockedPlayers = json.get("lockedPlayers")
    players = json.get("players")
    rules = json.get("rules")
    gameType = json.get("gameType")
    session["sport"] = SPORT_ID_TO_PYDFS_SPORT[json.get("sport")]

    optimizer = get_optimizer(
        is_captain_mode(gameType), session.get("sport")["sport"])
    optimizer.load_players([transform_player(player, gameType)
                            for player in players])

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

        return exported_json
    except LineupOptimizerException as exception:
        return Response(
            exception.message,
            status=500,
        )


@application.route("/export")
def exportCSV():
    try:
        if "lineups" in session:
            lineups = session.get("lineups")
            sport = session.get("sport")

            csv = generate_csv_from_csv(lineups, sport)

            return Response(csv,
                            mimetype="text/csv",
                            headers={"Content-disposition":
                                     "attachment; filename=DKSalaries.csv"})
    except:
        return Response(
            'Unable to generate CSV',
            status=500,
        )
