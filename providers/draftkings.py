import pandas as pd
import requests
from draft_kings import Client, data
from pydfs_lineup_optimizer import Site, Sport, get_optimizer
from utils import transform_lineups, transform_player, transform_to_json

BASE_URL = 'https://www.draftkings.com'
API_BASE_URL = 'https://api.draftkings.com'

class Draftkings:
    client: Client

    def __init__(self):
        self.client = Client()

    def get_sports(self):
        return list(self.__transform_sports())

    def get_contests(self, sport: str):
        return transform_to_json(self.client.contests(sport=data.CONTEST_SPORT_ABBREVIATIONS_TO_SPORTS[sport.upper()]).contests)

    def get_players(self, id):
        players = self.__get_players(id)
        # statuses = {player["status"] for player in players}

        return { 
            "players": players, 
            "statusFilters": [] # TODO: Get statuses
        }

    def get_optimized_lineups(self, sport, players, settings):
        transformedPlayers = players

        if (len(settings["statusFilters"])):
            transformedPlayers = filter(lambda player: player["status"] in settings["statusFilters"] , players)

        optimizer = get_optimizer(Site.DRAFTKINGS, DRAFTKINGS_SPORT_ID_TO_PYDFS_SPORT[sport['sportId']]['sport'])
        optimizer.player_pool.load_players([transform_player(player, None) for player in transformedPlayers])

        return transform_lineups(list(optimizer.optimize(n=settings["numberOfLineups"])), players)

    # Utils
    def __transform_sports(self):
        return map(
            (lambda sport: {
                **sport,
                "supported": sport["sportId"] in DRAFTKINGS_SPORT_ID_TO_PYDFS_SPORT,
                # "positions": SPORT_ID_TO_PYDFS_SPORT[sport["sportId"]]["positions"] if sport["sportId"] in SPORT_ID_TO_PYDFS_SPORT else None
            }), requests.get(f"{API_BASE_URL}/sites/US-DK/sports/v1/sports?format=json").json()["sports"])

    def __get_players(self, id):
        csv_players = self.get_available_players(id)
        draftable_players = transform_to_json(self.client.draftables(id).players)
       
        return [self.__merge_draftking_players(draftable_players, player) for index, player in csv_players.iterrows()]

    def __merge_draftking_players(self, draftable_players, player):
        found_player = next(filter(lambda x: x["draftable_id"] == player["ID"], draftable_players), None)

        return {
            "id": player["ID"],
            "first_name": found_player["name_details"]["first"],
            "last_name": found_player["name_details"]["last"],
            "position": found_player["position_name"],
            "team": found_player["team_details"]["abbreviation"],
            "salary": player["Salary"],
            "points_per_contest": player["AvgPointsPerGame"],
            "draft_positions": player["Roster Position"],
            # "status": found_player["status"], TODO: Add this
            "images": found_player["image_details"]
        }

    def get_available_players(self, draft_group_id):
        contest_id = self.client.draft_group_details(draft_group_id).contest_details.type_id
        url = f'{BASE_URL}/lineup/getavailableplayerscsv?contestTypeId={contest_id}&draftGroupId={draft_group_id}'

        df = pd.read_csv(url)
        df.head()

        return df


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