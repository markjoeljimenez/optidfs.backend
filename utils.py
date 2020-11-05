import csv
import pydash
import io
import pandas as pd
from pydfs_lineup_optimizer import Player, Sport
from pydfs_lineup_optimizer.constants import PlayerRank
from draft_kings.client import draftables

SPORT_ID_TO_PYDFS_SPORT = {
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
}


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
        float(player["salary"]),
        float(player["points_per_contest"]),
        player.get("status") == "O",
        PlayerRank.REGULAR,
        None,
        player.get("min_exposure"),
        player.get("projected_ownership")
    )

    return player


def transform_player_from_csv(player):
    player = Player(
        player["ID"],
        player['Name'].split()[0],
        player['Name'].split()[1] if len(player['Name'].split()) > 1 else '',
        player["Position"].split("/"),
        player["TeamAbbrev"],
        float(player["Salary"]),
        float(player["AvgPointsPerGame"]),
        # True if player["status"] == "O" else False,
        False,
        PlayerRank.REGULAR,
        None,
        # player["min_exposure"] if "min_exposure" in player else None,
        # player["projected_ownership"] if "projected_ownership" in player else None
        None,
        None
    )

    return player


def get_positions(sport):
    if sport == 'NFL':
        return Positions.NFL

    if sport == 'NBA':
        return Positions.NBA

    if sport == 'NHL':
        return Positions.NHL

    if sport == 'MLB':
        return Positions.MLB

    if sport == 'SOCCER':
        return Positions.SOCCER


def generate_csv(lineups, draft_group_id, sport):
    def get_draftable_id(id):
        # return pydash.find(draftables(draft_group_id)["draftables"], lambda _player: _player["player_id"] == id)["id"]
        # For some reason on production, 'id' is 'player_id' and 'draftable_id' is 'id'
        return pydash.find(draftables(draft_group_id)["draftables"], lambda _player: _player["id"] == id)["draftable_id"]

    positions = get_positions(sport)

    # csv = pd.DataFrame([get_draftable_id(player)
    #                     for player in lineups[0]["players"]], columns=list(positions))

    csvfile = io.StringIO()
    lineup_writer = csv.writer(csvfile, delimiter=',')

    for index, lineup in enumerate(lineups):
        if index == 0:
            header = [pos for pos in sport["positions"]]
            lineup_writer.writerow(header)
        row = [get_draftable_id(player) for player in lineup["players"]]
        lineup_writer.writerow(row)

    return csvfile.getvalue()


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
