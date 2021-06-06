"""Defines GameData and functions to read it."""

from bs4 import BeautifulSoup
import functools
from multipledispatch import dispatch

import cache
import scraper_tools
from shared_types import *


def _load_game_data_online(game: Game) -> GameData:
  """Reads a play-by-play page from CBS, given the date and teams.

  Keeps only "relevant" plays.  Each play has the format "<time> <type> <team>".
  Where <time> is the number of seconds from the start of the period; type is
  either "FO" for face-off or "SHOT" for a shot taken or "EOP" for end of
  period; and team is the team that won the face-off or took the shot.  (For
  EOP, no team is listed.)
  """
  PBP_URL = "https://www.cbssports.com/nhl/gametracker/playbyplay/NHL_{}_{}@{}"
  url = PBP_URL.format(game.date, game.away, game.home)

  print(f"Downloading {url}")

  html = scraper_tools.read_url_to_string(url)

  soup = BeautifulSoup(html, features="html.parser")

  started_pbp = False  # Don't start reading until first end-of-period
  result_pbp = list()
  period = 0

  tables = soup.find_all("ul", {
    "class": "gametracker-list gametracker-list--play-by-play"})
  for table in tables:
    for row in table.find_all("li"):
      spans = row.find_all("span")
      row = [span.text for span in spans]

      if row and row[-1] == "End of ":  # End of game or period
        period -= 1
        started_pbp = True
        result_pbp.append(Play(
          game=game,
          hockey_time=HockeyTime.from_str(period, "20:00"),
          type=Play.Type.end_of_period,
        ))

      if not started_pbp or len(row) != 5:
        continue

      hockey_time = HockeyTime.from_str(period, row[3])

      this_play_type = None
      if row[4].find("GOAL") != -1:  # Case sensitive
        this_play_type = Play.Type.goal
      elif row[4].lower().find("faceoff") != -1:
        this_play_type = Play.Type.face_off
      elif row[4].lower().find("shot") != -1:
        this_play_type = Play.Type.shot

      if this_play_type:
        result_pbp.append(Play(
          game=game, hockey_time=hockey_time, type=this_play_type, team=row[2]))

  # period is recorded as -1..-3 or -1..-N in the event of overtimes.  Remap -N
  #  to 1.
  pbp = list()
  for play in reversed(result_pbp):
    play.hockey_time.period += 1 - period
    pbp.append(play)

  return GameData(game=game, pbp=pbp)


# NOTE:  Caching logic for the functions below makes it difficult to delete
#  stale data.  Sub BasicCacher for NoCacher to remove this logic.


@functools.lru_cache(1500)
def load_game_data(game: Game) -> GameData:
  """Returns GameData for the game.

  If this exists on disk, then will load that.  Otherwise pulls from CBS.
  """
  print(f"Try load game: {str(game)}")
  @cache.memoize(str(game), cache.BasicCacher())
  def load_game_data_online():
    return _load_game_data_online(game)

  return load_game_data_online()


@dispatch(Date)
def get_games(date: Date) -> List[Game]:
  """List of games for a date."""

  print(f"Looking games for date {date}")

  @cache.memoize(f"GAMES_FOR_DATE_{date}", cache.BasicCacher())
  def get_games_for_date_impl():
    SCHED_URL = "https://www.cbssports.com/nhl/schedule/{}/"
    html = scraper_tools.read_url_to_string(SCHED_URL.format(date))
    soup = BeautifulSoup(html, features="html.parser")

    games = list()
    table = soup.find("div", id="TableBase")

    # If the date has no games, then this table won't exist.
    if not table:
      return []

    for tr in table.find_all("tr", {"class": "TableBase-bodyTr"}):
      try:
        away_team, home_team = None, None
        for tdi, td in enumerate(tr.find_all("td", {"class": "TableBase-bodyTd"})):
          if tdi == 0:
            away_link = td.find("a")["href"]
            away_team = away_link.split("teams/")[1].split("/")[0]
          if tdi == 1:
            home_link = td.find("a")["href"]
            home_team = home_link.split("teams/")[1].split("/")[0]
          if tdi > 2:
            break

        assert (away_team)
        assert (home_team)
        games.append(Game(date=date, away=away_team, home=home_team))
      except:
        pass

    return games

  return get_games_for_date_impl()


@dispatch(Season)
def get_games(season: Season) -> List[Game]:
  """List of games for a season."""
  result = list()
  for date in season.get_all_dates():
    for game in get_games(date):
      result.append(game)
  return result


@dispatch(Date)
def get_games_data(date: Date) -> Iterable[GameData]:
  """Read all games on a given date, storing to their respective files."""
  for game in get_games(date):
    yield load_game_data(game)


@dispatch(Season)
def get_games_data(season: Season) -> Iterable[GameData]:
  """Read all games in a given season, storing to their respective files."""
  for game in get_games(season):
    yield load_game_data(game)


def make_dataset(season: Season, test_portion: float = 0.2) -> TrainTest:
  assert(0 < test_portion < 1.0)

  train_portion = 1.0 - test_portion

  games = get_games(season)
  cutoff = int(len(games) * train_portion)
  return TrainTest(train=games[:cutoff], test=games[cutoff:])
