"""Defines GameData and functions to read it."""

import enum
import os
import pickle
from typing import Dict, Optional, Set

from bs4 import BeautifulSoup

import cache
from constants import *
import scraper_tools
from shared_types import *


@attr.s
class Play(object):
  """Various plays to be stored in the play-by-play."""

  class Type(enum.Enum):
    end_of_period = 1
    goal = 2
    face_off = 3
    shot = 4  # Shot not resulting in a goal.

  game: Game = attr.ib()
  hockey_time: HockeyTime = attr.ib()
  type: Type = attr.ib()
  # If type is goal or shot, refers to the team shooting.  If type is face_off,
  #  refers to the team that wins the face off.
  team: Optional[Team] = attr.ib(default=None)


class GameData(object):
  """Includes a play-by-play, and some lazily calculated meta-stats."""

  def __init__(self, game: Game, pbp: List[Play]):
    self.game = game
    self.pbp = pbp  # Play-by-play sorted by time-in-game

    # Don't calculate these until they're asked for.
    self._away_att, self._home_att = None, None
    self._away_score, self._home_score = None, None
    self._winner, self._tie = None, False

  def _count_plays_by_team(self, types: Set[Play.Type]) -> Dict[Team, int]:
    result = {self.game.away: 0, self.game.home: 0}
    for play in self.pbp:
      if play.type in types:
        result[play.team] += 1
    return result

  def _compute_atts(self):
    """Sets away_att and home_att."""
    atts = self._count_plays_by_team({Play.Type.shot, Play.Type.goal})
    self._away_att, self._home_att = atts[self.game.away], atts[self.game.home]

  def _compute_scores(self):
    """Sets home_score, away_score, winner, and tie."""
    scores = self._count_plays_by_team({Play.Type.goal})

    self._away_score, self._home_score = scores[self.game.away], scores[
      self.game.home]

    if self._away_score < self._home_score:
      self._winner = self.game.home
    elif self._away_score > self._home_score:
      self._winner = self.game.away
    else:
      self._tie = True

  @property
  def away_att(self):
    if self._away_att is None:
      self._compute_atts()

    return self._away_att

  @property
  def home_att(self):
    if self._home_att is None:
      self._compute_atts()

    return self._home_att

  @property
  def away_score(self):
    if self._away_score is None:
      self._compute_scores()

    return self._away_score

  @property
  def home_score(self):
    if self._home_score is None:
      self._compute_scores()

    return self._home_score

  @property
  def winner(self):
    if self._winner is None and not self._tie:
      self._compute_scores()

    return self._winner  # May be None still.


def _load_game_data_online(game: Game) -> GameData:
  """Reads a play-by-play page from CBS, given the date and teams.

  Keeps only "relevant" plays.  Each play has the format "<time> <type> <team>".
  Where <time> is the number of seconds from the start of the period; type is
  either "FO" for face-off or "SHOT" for a shot taken or "EOP" for end of
  period; and team is the team that won the face-off or took the shot.  (For
  EOP, no team is listed.)
  """
  PBP_URL = "https://www.cbssports.com/nhl/gametracker/playbyplay/NHL_{}_{}@{}"

  with scraper_tools.read_url_to_string(
      PBP_URL.format(game.date, game.away, game.home)) as f:
    html = f.read().decode("utf-8")

  soup = BeautifulSoup(html)

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


def load_game_data(game: Game) -> GameData:
  """Returns GameData for the game.

  If this exists on disk, then will load that.  Otherwise pulls from CBS.
  """
  @cache.memoize(game, cache.BasicCacher())
  def load_game_data_online():
    _load_game_data_online(game)

  return load_game_data_online()
