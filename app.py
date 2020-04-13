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
		player[0],
		player[1],
		player[2],
		player[3].split("/"),
		player[4],
		player[5],
		player[6],
		# True if player["status"] == "O" else False,
		player[7] if player[7] != "O" else None,
		# False
	)

	return player


# @app.route("/")
# def get_contests():
# 	with sqlite3.connect("players.db") as conn:
# 		c = conn.cursor()

# 		c.execute("DROP TABLE IF EXISTS players")

# 		c.execute("""CREATE TABLE players (
# 				id integer,
# 				first_name text,
# 				last_name text,
# 				position text,
# 				team text,
# 				salary integer,
# 				points_per_contest real,
# 				status text
# 				)""")

# 		conn.commit()

# 	return jsonpickle.encode(contests(sport=SportAPI.NBA))


@app.route("/players")
def get_players():
	with sqlite3.connect("players.db") as conn:
		c = conn.cursor()

		# Delete content in players table
		c.execute("delete from players")

		# Get id in url query
		draftId = request.args.get("id")

		# Get players
		# draftables = available_players(draftId)

		for player in draftables["players"]:
			c.execute("""INSERT INTO players VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (
				player["id"],
				player["first_name"],
				player["last_name"],
				player["position"]["name"],
				player["team"],
				player["draft"]["salary"],
				player["points_per_contest"],
				player["status"]
			))

		c.execute("SELECT * FROM players")

		return json.dumps({
			"players": [{
				"id": player[0],
				"first_name": player[1],
				"last_name": player[2],
				"position": player[3],
				"team": player[4],
				"salary": player[5],
				"points_per_contest": player[6],
				"status": player[7]
			} for player in c.fetchall()]
		})


# @app.route("/optimize", methods=["GET", "POST"])
@app.route("/")
def optimize():
	with sqlite3.connect("players.db") as conn:
		# c = conn.cursor()

		# # Get all players in db
		# c.execute("SELECT * FROM players")

		optimizer = get_optimizer(Site.DRAFTKINGS, Sport.BASKETBALL)
		# optimizer.load_players([transform_player(player) for player in c.fetchall()])
		optimizer.load_players_from_csv("DKSalaries.csv")

		response = {
			"success": True,
			"message": None
		}

		try:
			optimize = optimizer.optimize(1)
			exporter = JSONLineupExporter(optimize)
			exportedJSON = exporter.export()
			return merge_two_dicts(exportedJSON, response)
		except LineupOptimizerException as exception:
			response["success"] = False
			response["message"] = exception.message
			return response


@app.route("/stats")
def stats():
	playerId = players.find_players_by_full_name(request.args.get('player'))[0].get('id', None)

	player_info = json.loads(commonplayerinfo.CommonPlayerInfo(player_id=playerId).get_normalized_json()).get('CommonPlayerInfo', None)[0]
	player_headline_stats = json.loads(commonplayerinfo.CommonPlayerInfo(player_id=playerId).get_normalized_json()).get('PlayerHeadlineStats', None)[0]

	player_stats = json.loads(playerprofilev2.PlayerProfileV2(per_mode36="PerGame", player_id=playerId).get_normalized_json())

	teamId = player_info.get('TEAM_ID', None)

	profile_picture = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/%s/2019/260x190/%s.png" % (teamId, playerId)

	return { 
		**player_info,
		**player_headline_stats,
		**player_stats,
		"profile_picture": profile_picture
	}
