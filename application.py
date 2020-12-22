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
from utils import SPORT_ID_TO_PYDFS_SPORT, transform_player, merge_two_dicts, generate_csv, generate_csv_from_csv

application = Flask(__name__)
application.debug = True
application.config["SECRET_KEY"] = environ.get("SECRET_KEY")
application.config["SESSION_COOKIE_HTTPONLY"] = False
application.config["SESSION_COOKIE_SAMESITE"] = None

CORS(application, supports_credentials=True)


@application.route("/")
def get_sports():
    response = list(map(
        (lambda sport: {
            **sport,
            "supported": sport["sportId"] in SPORT_ID_TO_PYDFS_SPORT,
            "positions": SPORT_ID_TO_PYDFS_SPORT[sport["sportId"]]["positions"] if sport["sportId"] in SPORT_ID_TO_PYDFS_SPORT else None
        }), sports()["sports"]))

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
    if request.args.get("id"):
        # Get players
        players = available_players(request.args.get("id"))["players"]

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
            } for player in players]
        })

    if request.files:
        df = pd.read_csv(request.files.get("csv"))

        return json.dumps({
            "players": [{
                "id": player["ID"],
                "first_name": player["Name"].split()[0],
                "last_name": player["Name"].split()[1] if len(player["Name"].split()) > 1 else "",
                # NTS: player["Position"] is changing to player["Roster Position"] due to "FLEX"
                "position": player["Position"],
                "team": player["TeamAbbrev"],
                "salary": player["Salary"],
                "points_per_contest": player["AvgPointsPerGame"],
            } for index, player in df.iterrows()]
        })

    return {}


@application.route("/optimize", methods=["GET", "POST"])
def optimize():
    json = request.get_json()

    lockedPlayers = json.get("lockedPlayers")
    players = json.get("players")
    rules = json.get("rules")
    stacking = json.get("stacking")
    session["sport"] = json.get("sport")
    session["draftGroupId"] = json.get("draftGroupId")

    optimizer = get_optimizer(
        Site.DRAFTKINGS, SPORT_ID_TO_PYDFS_SPORT[session.get("sport")]["sport"])
    optimizer.load_players([transform_player(player)
                            for player in players])
    # print(stacking)

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

    if "TEAM" in stacking:
        team = stacking["TEAM"]

        if "NUMBER_OF_PLAYERS_TO_STACK" in team:
            optimizer.add_stack(
                TeamStack(team["NUMBER_OF_PLAYERS_TO_STACK"],
                          for_teams=team["FROM_TEAMS"] if "FROM_TEAMS" in team else None,
                          for_positions=team["FROM_POSITIONS"] if "FROM_POSITIONS" in team else None,
                          spacing=team["SPACING"] if "SPACING" in team else None,
                          max_exposure=team["MAX_EXPOSURE"] if "MAX_EXPOSURE" in team else None,
                          max_exposure_per_team={
                    team["MAX_EXPOSURE_PER_TEAM"]["team"]: team["MAX_EXPOSURE_PER_TEAM"]["exposure"]} if "MAX_EXPOSURE_PER_TEAM" in team else None
                )
            )

    if "POSITION" in stacking:
        position = stacking["POSITION"]

        if "NUMBER_OF_POSITIONS" in position:
            optimizer.add_stack(PositionsStack(
                position["NUMBER_OF_POSITIONS"],
                for_teams=position["FOR_TEAMS"] if "FOR_TEAMS" in position else None,
                max_exposure=position["MAX_EXPOSURE"] if "MAX_EXPOSURE" in position else None),
                max_exposure_per_team={position["MAX_EXPOSURE_PER_TEAM"]["team"]: position["MAX_EXPOSURE_PER_TEAM"]["exposure"]} if "MAX_EXPOSURE_PER_TEAM" in position else None),

    if "CUSTOM" in stacking:
        custom = stacking["CUSTOM"]

        if "STACKS" in custom:
            stacks = [player["players"] for player in custom["STACKS"]]

            groups = []

            for stack in stacks:
                players = []

                for player in stack:
                    players.append(optimizer.get_player_by_name(
                        f'{player["first_name"]} {player["last_name"]}'))

            if (len(groups) > 1):
                optimizer.add_stack(Stack([groups]))

            # Only get first stack for now
            # stacks = custom["STACKS"][0]

            # if "players" in stacks:
            #     players = stacks["players"]

            #     group = PlayersGroup([
            #         optimizer.get_player_by_name(f'{player["first_name"]} {player["last_name"]}') for player in players])

            #     print(group)

            #     optimizer.add_stack(Stack([group]))

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


@ application.route("/export")
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
            status=400,
        )
