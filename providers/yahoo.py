from pydfs_lineup_optimizer import Site, Sport, get_optimizer
import requests
from utils import remove_duplicates, transform_lineups, transform_player

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
        players = requests.get(PLAYERS(id)).json()["players"]["result"]
        statuses = {player["status"] for player in players}

        return { 
            "players": players, 
            "statusFilters": statuses 
        }

    def get_optimized_lineups(self, sport, players, settings):
        transformedPlayers = players

        if (len(settings["statusFilters"])):
            transformedPlayers = filter(lambda player: player["status"] in settings["statusFilters"] , players)

        optimizer = get_optimizer(Site.YAHOO, YAHOO_SPORT_ID_TO_PYDFS_SPORT[sport['sportId']]['sport'])
        optimizer.player_pool.load_players([transform_player(player, None) for player in transformedPlayers])

        return transform_lineups(list(optimizer.optimize(n=settings["numberOfLineups"])), players, [position.name for position in optimizer.settings.positions])

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

YAHOO_SPORT_ID_TO_PYDFS_SPORT = {
    "golf": { "sport": Sport.GOLF },
    "mlb": { "sport": Sport.BASEBALL }
}