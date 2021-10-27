from utils import SPORT_ID_TO_PYDFS_SPORT, get_available_players, is_captain_mode
from draft_kings.client import contests, sports
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
        "players": lambda id: ({
            "provider": "draftkings",
            "players": [{
                "id": player["ID"],
                "first_name": player["Name"].split()[0],
                "last_name": player["Name"].split()[1] if len(player["Name"].split()) > 1 else "",
                "position": player["Position"],
                "team": player["TeamAbbrev"],
                "salary": player["Salary"],
                "points_per_contest": round(player["AvgPointsPerGame"] * (1.5 if player["Roster Position"] == 'CPT' else 1), 2),
                "draft_positions": player["Roster Position"]
            } for index, player in get_available_players(id).iterrows()]
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
        "players": lambda id: ({
            "provider": "yahoo",
            "players": requests.get(yahoo_players(id)).json()["players"]["result"]
        }),
        "optimize": lambda sport, gameType: get_optimizer(Site.YAHOO, SPORT_ID_TO_PYDFS_SPORT[sport["sportId"]]["sport"])
    }
}