from pydfs_lineup_optimizer import Site, get_optimizer
import requests
from utils import YAHOO_SPORT_ID_TO_PYDFS_SPORT, remove_duplicates, transform_lineups, transform_player

YAHOO_ENDPOINT = "https://dfyql-ro.sports.yahoo.com/v2"

CONTESTS = lambda sport: f'{YAHOO_ENDPOINT}/contestsFilteredWeb?sport={sport}'
ALL_CONTESTS = f'{YAHOO_ENDPOINT}/contestsFilteredWeb'
PLAYERS = lambda contestId: f'{YAHOO_ENDPOINT}/contestPlayers?contestId={contestId}'

class Yahoo:
    def get_sports(self):
        return remove_duplicates(self.__map_contests_to_sports(requests.get(ALL_CONTESTS).json()["contests"]["result"]))

    def get_contests(self, sport: str):
        return requests.get(CONTESTS(sport.lower())).json()["contests"]["result"]

    def get_players(self, id):
        return requests.get(PLAYERS(id)).json()["players"]["result"]

    def get_optimized_lineups(self, sport, players, settings):
        optimizer = get_optimizer(Site.YAHOO, YAHOO_SPORT_ID_TO_PYDFS_SPORT[sport['sportId']]['sport'])
        optimizer.player_pool.load_players([transform_player(player, None) for player in players])

        return transform_lineups(list(optimizer.optimize(n=settings["numberOfLineups"])), players)

    # Utils
    def __map_contests_to_sports(self, contests):
        return map(
            (lambda contest: {
                "fullName": contest["sportCode"],
                "sportId": contest["sportCode"],
                "hasPublicContests": True,
                "supported": True,
                "isEnabled": True,
            }), contests)
