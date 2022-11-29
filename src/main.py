from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from modules.providers.draftkings import Draftkings
from modules.providers.yahoo import Yahoo
from modules.utils import transform_player, transform_lineups

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

providers = {
    'yahoo': Yahoo(),
    'draftkings': Draftkings()
}

@app.get("/")
async def get_sports(provider: str):
    try:
        return providers.get(provider).get_sports()
    except:
        raise HTTPException(status_code=500, detail="Unable to reach servers")


@app.get("/contests")
async def contests(provider, sport, sportId):
    try:
        return providers.get(provider).get_contests(sportId if provider == 'yahoo' else sport)
    except:
        raise HTTPException(status_code=500, detail="Unable to get contests")

@app.get("/players")
async def get_players(id, provider):
    try:
        return providers.get(provider).get_players(id)
    except:
        raise HTTPException(status_code=500, detail="Unable to get players")

@app.post("/optimize")
async def optimize(request: Request):
    body = await request.json()

    players = body['players']
    provider = body['provider']
    sport = body['sport']
    settings = body['settings']

    transformedPlayers = players

    try:
        if (len(settings["statusFilters"])):
                transformedPlayers = filter(lambda player: player["status"] in settings["statusFilters"], players)

        optimizer = providers.get(provider).get_optimizer(sport)
        optimizer.player_pool.load_players([transform_player(player, None) for player in transformedPlayers])

        if (len(settings["lockedPlayers"])):
                for player in settings["lockedPlayers"]:
                    optimizer.player_pool.lock_player(player)

        if (len(settings["excludedPlayers"])):
                for player in settings["excludedPlayers"]:
                    optimizer.player_pool.remove_player(player)

        max_exposure = settings["maximumExposure"] if "maximumExposure" in settings else None

        return transform_lineups(
            list(optimizer.optimize(n=settings["numberOfLineups"], max_exposure=max_exposure)), 
            players, 
            [position.name for position in optimizer.settings.positions])
    except Exception as e:
        raise HTTPException(status_code=500, detail=e.__str__())



# @ application.route("/players", methods=["GET", "POST"])
# def get_players():
#     try:
#         contestId = request.args.get("id")
#         provider =  request.args.get("provider")
#         gameType = request.args.get("gameType")

#         if contestId:
#             players = providers[provider]["players"](contestId, gameType)

#             return json.dumps(players)

#         if request.files:
#             df = pd.read_csv(request.files.get("csv"))

#             return json.dumps({
#                 "players": [{
#                     "id": player["ID"],
#                     "first_name": player["Name"].split()[0],
#                     "last_name": player["Name"].split()[1] if len(player["Name"].split()) > 1 else "",
#                     "position": player["Position"],
#                     "team": player["TeamAbbrev"],
#                     "salary": player["Salary"],
#                     "points_per_contest": player["AvgPointsPerGame"],
#                     "draft_positions": player["Roster Position"]
#                 } for index, player in df.iterrows()]
#             })
#     except:
#         return Response(
#             "Unable to get players",
#             status=500,
#         )


# @application.route("/optimize", methods=["GET", "POST"])
# def optimize():
#     json = request.get_json()

#     players = json.get("players")
#     rules = json.get("rules")
#     gameType = json.get("gameType")
#     stacking = json.get("stacking")
#     provider =  json.get("provider")
#     session["sport"] = json.get("sport")

#     # session["draftGroupId"] = json.get("draftGroupId")

#     optimizer = providers[provider]["optimize"](session["sport"], gameType)
#     optimizer.load_players([transform_player(player, gameType)
#                             for player in players["all"]])

#     if "locked" in players and players['locked'] is not None:
#         for player in players['locked']:
#             optimizer.add_player_to_lineup(optimizer.get_player_by_id(player))

#     if "excluded" in players and players["excluded"] is not None:
#         for player in players['excluded']:
#             optimizer.remove_player(optimizer.get_player_by_id(player))

#     if "NUMBER_OF_PLAYERS_TO_STACK_FROM_SAME_TEAM" in rules:
#         for team in rules["NUMBER_OF_PLAYERS_TO_STACK_FROM_SAME_TEAM"]:
#             optimizer.set_players_from_one_team({
#                 team["key"]: team["value"]
#             })

#     if "NUMBER_OF_SPECIFIC_POSITIONS" in rules:
#         for position in rules["NUMBER_OF_SPECIFIC_POSITIONS"]:
#             optimizer.set_players_with_same_position({
#                 position["key"]: position["value"]
#             })

#     if "MINIMUM_SALARY_CAP" in rules:
#         optimizer.set_min_salary_cap(rules["MINIMUM_SALARY_CAP"])

#     if "MAX_REPEATING_PLAYERS" in rules:
#         optimizer.set_max_repeating_players(
#             rules["MAX_REPEATING_PLAYERS"])

#     if "MAX_PROJECTED_OWNERSHIP" in rules or "MIN_PROJECTED_OWNERSHIP" in rules:
#         optimizer.set_projected_ownership(
#             min_projected_ownership=rules["MIN_PROJECTED_OWNERSHIP"] if "MIN_PROJECTED_OWNERSHIP" in rules else None, max_projected_ownership=rules["MAX_PROJECTED_OWNERSHIP"] if "MAX_PROJECTED_OWNERSHIP" in rules else None)

#     if stacking: 
#         if "TEAM" in stacking:
#             team = stacking["TEAM"]

#             if "NUMBER_OF_PLAYERS_TO_STACK" in team:
#                 optimizer.add_stack(
#                     TeamStack(team["NUMBER_OF_PLAYERS_TO_STACK"],
#                             for_teams=team["FROM_TEAMS"] if "FROM_TEAMS" in team else None,
#                             for_positions=team["FROM_POSITIONS"] if "FROM_POSITIONS" in team else None,
#                             spacing=team["SPACING"] if "SPACING" in team else None,
#                             max_exposure=team["MAX_EXPOSURE"] if "MAX_EXPOSURE" in team else None,
#                             max_exposure_per_team={
#                         team["MAX_EXPOSURE_PER_TEAM"]["team"]: team["MAX_EXPOSURE_PER_TEAM"]["exposure"]} if "MAX_EXPOSURE_PER_TEAM" in team else None
#                     )
#                 )

#         if "POSITION" in stacking:
#             position = stacking["POSITION"]

#             if "NUMBER_OF_POSITIONS" in position:
#                 optimizer.add_stack(PositionsStack(
#                     position["NUMBER_OF_POSITIONS"],
#                     for_teams=position["FOR_TEAMS"] if "FOR_TEAMS" in position else None,
#                     max_exposure=position["MAX_EXPOSURE"] if "MAX_EXPOSURE" in position else None),
#                     max_exposure_per_team={position["MAX_EXPOSURE_PER_TEAM"]["team"]: position["MAX_EXPOSURE_PER_TEAM"]["exposure"]} if "MAX_EXPOSURE_PER_TEAM" in position else None),

#         if "CUSTOM" in stacking:
#             custom = stacking["CUSTOM"]

#             if "STACKS" in custom:
#                 stacks = [player["players"] for player in custom["STACKS"]]

#                 groups = []

#                 for stack in stacks:
#                     players = []

#                     for player in stack:
#                         players.append(optimizer.get_player_by_name(
#                             f'{player["first_name"]} {player["last_name"]}'))

#                 if (len(groups) > 1):
#                     optimizer.add_stack(Stack([groups]))

#                 # Only get first stack for now
#                 # stacks = custom["STACKS"][0]

#                 # if "players" in stacks:
#                 #     players = stacks["players"]

#                 #     group = PlayersGroup([
#                 #         optimizer.get_player_by_name(f'{player["first_name"]} {player["last_name"]}') for player in players])

#                 #     print(group)

#                 #     optimizer.add_stack(Stack([group]))

#     try:
#         optimize = optimizer.optimize(rules["NUMBER_OF_GENERATIONS"])

#         exporter = JSONLineupExporter(optimize)
#         exported_json = exporter.export()

#         session["lineups"] = exported_json["lineups"]

#         return exported_json
#     except LineupOptimizerException as exception:
#         return Response(
#             exception.message,
#             status=500,
#         )


# @application.route("/export")
# def exportCSV():
#     try:
#         if "lineups" in session:
#             lineups = session.get("lineups")
#             sport = session.get("sport")

#             csv = generate_csv_from_csv(
#                 lineups, SPORT_ID_TO_PYDFS_SPORT[sport["sportId"]])

#             return Response(csv,
#                             mimetype="text/csv",
#                             headers={"Content-disposition":
#                                      "attachment; filename=DKSalaries.csv"})
#     except:
#         return Response(
#             'Unable to generate CSV',
#             status=500,
#         )
