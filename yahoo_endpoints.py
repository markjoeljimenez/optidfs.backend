ENDPOINT = "https://dfyql-ro.sports.yahoo.com/v2"

yahoo_contests = lambda sport: f'{ENDPOINT}/contestsFilteredWeb?&sport={sport}'
yahoo_players = lambda contestId: f'{ENDPOINT}/contestPlayers?contestId={contestId}'