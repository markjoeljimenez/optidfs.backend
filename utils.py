import csv
import pydash
import io
from pydfs_lineup_optimizer import Player, Sport
from pydfs_lineup_optimizer.constants import PlayerRank
from draft_kings.client import draftables
from positions import Positions


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


def get_sport(sport):
    if sport == 'NFL':
        return Sport.FOOTBALL

    if sport == 'NBA':
        return Sport.BASKETBALL

    if sport == 'NHL':
        return Sport.HOCKEY

    if sport == 'MLB':
        return Sport.BASEBALL

    if sport == 'SOCCER':
        return Sport.SOCCER


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
        return pydash.find(draftables(draft_group_id)["draftables"], lambda _player: _player["id"] == id)["draftable_id"]

    positions = get_positions(sport)

    csvfile = io.StringIO()
    lineup_writer = csv.writer(csvfile, delimiter=',')

    for index, lineup in enumerate(lineups):
        if index == 0:
            header = [pos for pos in positions]
            lineup_writer.writerow(header)
        row = [get_draftable_id(player) for player in lineup["players"]]
        lineup_writer.writerow(row)

    return csvfile
