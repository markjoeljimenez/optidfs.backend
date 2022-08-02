import csv
# import pydash
import io
import json
import jsonpickle
from pydfs_lineup_optimizer import Lineup, Player, Sport, Site
# from draft_kings.client import draftables, draft_group_details

def remove_duplicates(list):
    return [dict(t) for t in {tuple(sorted(d.items())) for d in list}]

def transform_to_json(a):
    return list(map(
                (lambda o: json.loads(jsonpickle.encode(o, unpicklable=False))), a)
            )


def transform_player(player, gameType):
    return Player(
        player["id"],
        player["firstName"],
        player["lastName"],
        player["draftPositions"].split("/") if gameType and 'Showdown' in gameType else player["position"].split("/"),
        player["team"],
        float(player["salary"]),
        float(player["fppg"]),
        # player.get("status") == "O",
        # None,
        # player.get("minExposure"),
        # player.get("projectedOwnership")
    )


# def generate_csv(lineups, draft_group_id, sport):
#     def get_draftable_id(id):
#         return pydash.find(draftables(draft_group_id)["draftables"], lambda _player: _player["id"] == id)["draftable_id"]

#     positions = get_positions(sport)

#     csvfile = io.StringIO()
#     lineup_writer = csv.writer(csvfile, delimiter=',')

#     for index, lineup in enumerate(lineups):
#         if index == 0:
#             header = [pos for pos in sport["positions"]]
#             lineup_writer.writerow(header)
#         row = [get_draftable_id(player) for player in lineup["players"]]
#         lineup_writer.writerow(row)

#     return csvfile.getvalue()


def generate_csv_from_csv(lineups, sport):
    csvfile = io.StringIO()
    lineup_writer = csv.writer(csvfile, delimiter=',')

    for index, lineup in enumerate(lineups):
        if index == 0:
            header = [pos for pos in sport["positions"]]
            lineup_writer.writerow(header)
        row = lineup["players"]
        lineup_writer.writerow(row)

    return csvfile.getvalue()


def is_captain_mode(gameType):
    return Site.DRAFTKINGS_CAPTAIN_MODE if 'Showdown' in gameType else Site.DRAFTKINGS

def transform_lineups(lineups: 'list[Lineup]', players, positions):
    _lineups = []

    for lineup in lineups:
        p = [next((player for i, player in enumerate(players) if player['id'] == l._player.id), None) for l in lineup]

        _lineups.append({
            'players': p,
            'fppg': lineup.fantasy_points_projection,
            'salary': lineup.salary_costs,
        })

    return { 
        'lineups': _lineups, 
        'positions': positions
    }