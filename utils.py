from pydfs_lineup_optimizer import Player, Sport
from pydfs_lineup_optimizer.constants import PlayerRank


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
