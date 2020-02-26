import json
import re
import requests
import jsonpickle
import sqlite3
from flask import Flask, request
from flask_restful import Api, Resource, reqparse
from flask_cors import CORS
from pydfs_lineup_optimizer import get_optimizer, Site, Sport, Player, LineupOptimizerException, JSONLineupExporter
from draft_kings.data import Sport as SportAPI
from draft_kings.client import contests, available_players, draftables, draft_group_details

app = Flask(__name__)
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
        # True if player["status"] == "O" else False,
        player["status"] if player["status"] != "O" else None,
        # False
    )

    return player


@app.route("/")
def get_contests():
    with sqlite3.connect("players.db") as conn:
        c = conn.cursor()

        # Drop table when user reconnects to the home page
        c.execute("""DROP TABLE IF EXISTS players""")

        # Create table
        c.execute("""CREATE TABLE players (
                id integer,
                first_name text,
                last_name text,
                position text,
                team text,
                salary integer,
                points_per_contest real
                )""")

        conn.commit()

    return jsonpickle.encode(contests(sport=SportAPI.NBA))


@app.route("/players")
def get_players():
    with sqlite3.connect("players.db") as conn:
        c = conn.cursor()

        c.execute(
            """ SELECT count(name) FROM sqlite_master WHERE type="table" AND name="players" """)

        # If db exists
        if c.fetchone()[0] == 1:
            # Get id in url query
            draftId = request.args.get("id")

            # Get players
            draftables = available_players(draftId)

            for player in draftables["players"]:
                c.execute("""INSERT INTO players VALUES (?, ?, ?, ?, ?, ?, ?)""", (
                    player["id"],
                    player["first_name"],
                    player["last_name"],
                    player["position"]["name"],
                    player["team"],
                    player["draft"]["salary"],
                    player["points_per_contest"]
                ))

        c.execute("SELECT * FROM players")

        players = c.fetchall()

        playerJSON = []

        for player in players:
            playerJSON.append({
                "id": player[0],
                "first_name": player[1],
                "last_name": player[2],
                "position": player[3],
                "team": player[4],
                "salary": player[5],
                "points_per_contest": player[6]
            })

        return json.dumps({
            "players": playerJSON
        })


@app.route("/optimize", methods=["GET", "POST"])
def optimize():
    # global draftables

    # lockedPlayers = request.json["locked"]
    # excludedPlayers = request.json["excluded"]

    players = [transform_player(player) for player in draftables["players"]]

    optimizer = get_optimizer(Site.DRAFTKINGS, Sport.BASKETBALL)
    optimizer.load_players(players)

    response = {
        "success": True,
        "message": None
    }

    # if lockedPlayers != None:
    #     for lockedPlayer in lockedPlayers:
    #         try:
    #             player = optimizer.get_player_by_id(lockedPlayer)
    #             optimizer.add_player_to_lineup(player)
    #         except LineupOptimizerException as exception:
    #             response["success"] = False
    #             response["message"] = exception.message
    #             return response

    # if excludedPlayers != None:
    #     for excludedPlayer in excludedPlayers:
    #         try:
    #             player = optimizer.get_player_by_id(excludedPlayer)
    #             optimizer.remove_player(player)
    #         except LineupOptimizerException as exception:
    #             response["success"] = False
    #             response["message"] = exception.message
    #             return response

    try:
        optimize = optimizer.optimize(1)
        exporter = JSONLineupExporter(optimize)
        exportedJSON = exporter.export()
        return merge_two_dicts(exportedJSON, response)
    except LineupOptimizerException as exception:
        response["success"] = False
        response["message"] = exception.message
        return response
