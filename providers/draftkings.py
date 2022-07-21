import requests
from draft_kings import Client, data
from pydfs_lineup_optimizer import Sport

from utils import remove_duplicates

API_BASE_URL = 'https://api.draftkings.com'

class Draftkings:
    def get_sports(self):
        return list(self.__transform_sports())

    def get_contests(self, sport: str):
        return remove_duplicates(list(
                    map(
                        (lambda contests: contests.__dict__), Client().contests(sport=data.CONTEST_SPORT_ABBREVIATIONS_TO_SPORTS[sport.upper()]).contests)
                    )
                )

    # Utils
    def __transform_sports(self):
        return map(
            (lambda sport: {
                **sport,
                "supported": sport["sportId"] in DRAFTKINGS_SPORT_ID_TO_PYDFS_SPORT,
                # "positions": SPORT_ID_TO_PYDFS_SPORT[sport["sportId"]]["positions"] if sport["sportId"] in SPORT_ID_TO_PYDFS_SPORT else None
            }), requests.get(f"{API_BASE_URL}/sites/US-DK/sports/v1/sports?format=json").json()["sports"])


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