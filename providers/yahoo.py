import requests
from utils import remove_duplicates

YAHOO_ENDPOINT = "https://dfyql-ro.sports.yahoo.com/v2"

CONTESTS = lambda sport: f'{YAHOO_ENDPOINT}/contestsFilteredWeb?sport={sport}'
ALL_CONTESTS = f'{YAHOO_ENDPOINT}/contestsFilteredWeb'
PLAYERS = lambda contestId: f'{YAHOO_ENDPOINT}/contestPlayers?contestId={contestId}'

class Yahoo:
    def get_sports(self):
        return remove_duplicates(self.__map_contests_to_sports(requests.get(ALL_CONTESTS).json()["contests"]["result"]))

    def get_contests(self, sport: str):
        return requests.get(CONTESTS(sport.lower())).json()["contests"]["result"]

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
