from utils import SPORT_ID_TO_PYDFS_SPORT, get_available_players, is_captain_mode
from draft_kings.client import contests, sports, draftables
from draft_kings.data import SPORT_ID_TO_SPORT
from yahoo_endpoints import yahoo_contests, yahoo_players
from pydfs_lineup_optimizer import get_optimizer, Site
import requests

providers = {
    "draftkings": {
        "sports": list(map(
            (lambda sport: {
                **sport,
                "supported": sport["sportId"] in SPORT_ID_TO_PYDFS_SPORT,
                "positions": SPORT_ID_TO_PYDFS_SPORT[sport["sportId"]]["positions"] if sport["sportId"] in SPORT_ID_TO_PYDFS_SPORT else None
            }), sports()["sports"])),
        "contests": lambda sportId, sport: ({ 
            "provider": "draftkings",
            "contests": contests(sport=SPORT_ID_TO_SPORT[sportId])["contests"],
        }),
        "players": lambda id, gameType: ({
            "provider": "draftkings",
            "players": get_draftkings_players(id)
        }),
        "optimize": lambda sport, gameType: get_optimizer(is_captain_mode(gameType), SPORT_ID_TO_PYDFS_SPORT[sport["sportId"]]["sport"])
    },
    "yahoo": {
        "sports": list([{
                "fullName": "Football",
                "hasPublicContests": True,
                "isEnabled": True,
                "positions": ["QB", "RB", "RB", "WR", "WR", "WR", "TE", "FLEX", "DST"],
                "regionAbbreviatedSportName": "NFL",
                "regionFullSportName": "Football",
                "sortOrder": 1,
                "sportId": 1,
                "supported": True
            }, {
                "fullName": "Basketball",
                "hasPublicContests": True,
                "isEnabled": True,
                "positions": ["PG", "SG", "SF", "PF", "C", "G", "F", "UTIL"],
                "regionAbbreviatedSportName": "NBA",
                "regionFullSportName": "Basketball",
                "sortOrder": 2,
                "sportId": 4,
                "supported": True
        }]),
        "contests": lambda sportId, sport: ({
            "provider": "yahoo",
            "contests": requests.get(yahoo_contests(sport.lower())).json()["contests"]["result"]
        }),
        "players": lambda id, gameType: ({
            "provider": "yahoo",
            "players": requests.get(yahoo_players(id)).json()["players"]["result"]
        }),
        "optimize": lambda sport, gameType: get_optimizer(Site.YAHOO, SPORT_ID_TO_PYDFS_SPORT[sport["sportId"]]["sport"])
    }
}

def get_draftkings_players(id):
    csv_players = get_available_players(id)
    return list([test_test(player, id) for index, player in csv_players.iterrows()])


def merge_draftking_players(player, id):
    draftable_players = draftables(id)["draftables"]
    found_player = next(filter(lambda x: x["id"] == player["ID"], draftable_players), None)
    return {
        "id": found_player["id"],
        "first_name": found_player["names"]["first"],
        "last_name": found_player["names"]["last"],
        "position": found_player["position"],
        "team": found_player["team_abbreviation"],
        "salary": found_player["salary"],
        "points_per_contest": player["AvgPointsPerGame"],
        "draft_positions": player["Roster Position"],
        "status": found_player["status"],
        "images": found_player["images"]
    }