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

DRAFTKINGS_SPORT_ID_TO_PYDFS_SPORT = {
    1: {
        "sport": Sport.FOOTBALL,
        "positions": ["QB", "RB", "RB", "WR", "WR", "WR", "TE", "FLEX", "DST"]
    },
    2: {
        "sport": Sport.BASEBALL,
        "positions": ["P", "P", "C", "1B", "2B", "3B", "SS", "OF", "OF", "OF"]
    },
    3: {
        "sport": Sport.HOCKEY,
        "positions": ["C", "C", "W", "W", "W", "D", "D", "G", "UTIL"]
    },
    4: {
        "sport": Sport.BASKETBALL,
        "positions": ["PG", "SG", "SF", "PF", "C", "G", "F", "UTIL"]
    },
    # # 6: Sport.BASKETBALL,  # Sport.COLLEGE_BASKETBALL
    # # 5: Sport.FOOTBALL,  # Sport.COLLEGE_FOOTBALL
    9: {
        "sport": Sport.MMA,
        "positions": ["F", "F", "F", "F", "F", "F"]
    },
    10: {
        "sport": Sport.NASCAR,
        "positions": ["D", "D", "D", "D", "D", "D"]
    },
    # 11: Sport.LEAGUE_OF_LEGENDS,
    12: {
        "sport": Sport.SOCCER,
        "positions": ["F", "F", "M", "M", "D", "D", "GK", "UTIL"]
    },
    13:  {
        "sport": Sport.GOLF,
        "positions": ["G", "G", "G", "G", "G", "G"]
    },
    # 14: Sport.CANADIAN_FOOTBALL,
    # # 15: Sport.BASKETBALL,  # Sport.EUROLEAGUE_BASKETBALL
    16: {
        "sport": Sport.TENNIS,
        "positions": ["P", "P", "P", "P", "P", "P"]
    },
    # # : Sport.ARENA_FOOTBALL_LEAGUE,
    19: {
        "sport": Sport.CS,
        "positions": ["CPT", "FLEX", "FLEX", "FLEX", "FLEX", "FLEX"]
    }
}

YAHOO_SPORT_ID_TO_PYDFS_SPORT = {
    "golf": { "sport": Sport.GOLF },
    "mlb": { "sport": Sport.BASEBALL }
}


# def merge_two_dicts(x, y):
#     z = x.copy()   # start with x"s keys and values
#     z.update(y)    # modifies z with y"s keys and values & returns None
#     return z


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


# def get_positions(sport):
#     if sport == 'NFL':
#         return Positions.NFL

#     if sport == 'NBA':
#         return Positions.NBA

#     if sport == 'NHL':
#         return Positions.NHL

#     if sport == 'MLB':
#         return Positions.MLB

#     if sport == 'SOCCER':
#         return Positions.SOCCER


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

def transform_lineups(lineups: 'list[Lineup]', players):
    _lineups = []

    for lineup in lineups:
        players = [next((player for player in players if player['id'] == l._player.id), None) for l in lineup]

        _lineups.append({
            'players': players,
            'fppg': lineup.fantasy_points_projection,
            'salary': lineup.salary_costs
        })

    return _lineups