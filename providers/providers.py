# from utils import SPORT_ID_TO_PYDFS_SPORT, get_available_players, is_captain_mode
import jsonpickle
from providers.draftkings import Draftkings
from providers.yahoo import Yahoo
from utils import DRAFTKINGS_SPORT_ID_TO_PYDFS_SPORT, YAHOO_SPORT_ID_TO_PYDFS_SPORT
# from draft_kings.client import contests, sports, draftables
from draft_kings import Sport, Client, data
# from draft_kings.data import SPORT_ID_TO_SPORT
from pydfs_lineup_optimizer import get_optimizer, Site
import requests

providers = {
    'yahoo': Yahoo(),
    'draftkings': Draftkings()
}

providers = {
    "draftkings": {
        "sports": list(map(
            (lambda sport: {
                **sport,
                "supported": sport["sportId"] in DRAFTKINGS_SPORT_ID_TO_PYDFS_SPORT,
                # "positions": SPORT_ID_TO_PYDFS_SPORT[sport["sportId"]]["positions"] if sport["sportId"] in SPORT_ID_TO_PYDFS_SPORT else None
            }), requests.get("https://api.draftkings.com/sites/US-DK/sports/v1/sports?format=json").json()["sports"])),
        "contests": lambda sport: get_draftkings_contests(sport)
        # "players": lambda id, gameType: ({
        #     "provider": "draftkings",
        #     "players": get_draftkings_players(id)
        # }),
        # "optimize": lambda sport, gameType: get_optimizer(is_captain_mode(gameType), SPORT_ID_TO_PYDFS_SPORT[sport["sportId"]]["sport"])
    },
    "yahoo": {
        "sports": providers.get('yahoo').get_sports(),
        "contests": lambda sport: providers.get('yahoo').get_contests(sport),
        # "players": lambda id, gameType: ({
        #     "provider": "yahoo",
        #     "players": requests.get(yahoo_players(id)).json()["players"]["result"]
        # }),
        # "optimize": lambda sport, gameType: get_optimizer(Site.YAHOO, DRAFTKINGS_SPORT_ID_TO_PYDFS_SPORT[sport["sportId"]]["sport"])
    }
}

# def get_draftkings_players(id):
#     csv_players = get_available_players(id)
#     draftable_players = draftables(id)["draftables"]
#     return list([merge_draftking_players(draftable_players, player, id) for index, player in csv_players.iterrows()])


# def merge_draftking_players(draftable_players, player, id):
#     found_player = next(filter(lambda x: x["id"] == player["ID"], draftable_players), None)
#     return {
#         "id": player["ID"],
#         "first_name": found_player["names"]["first"],
#         "last_name": found_player["names"]["last"],
#         "position": found_player["position"],
#         "team": found_player["team_abbreviation"],
#         "salary": found_player["salary"],
#         "points_per_contest": player["AvgPointsPerGame"],
#         "draft_positions": player["Roster Position"],
#         "status": found_player["status"],
#         "images": found_player["images"]
#     }

def get_draftkings_contests(sport):
    return [dict(t) for t in {tuple(sorted(d.items())) for d in list(map(
        (lambda contests: contests.__dict__), Client().contests(sport=data.CONTEST_SPORT_ABBREVIATIONS_TO_SPORTS[sport.upper()]).contests))
    }]