"""Includes some shared types.

Unlike other files, we will import as "from shared_types import *".
"""

import datetime
import enum
from typing import Dict, Iterable, List, Optional, Set

import attr

Date = int  # YYYYMMDD
Team = str
Url = str


@attr.s
class HockeyTime(object):
  period: int = attr.ib()
  secs: int = attr.ib()  # Seconds since the start of the period.

  @classmethod
  def from_str(cls, period: int, clock_time: str) -> 'HockeyTime':
    """From clock_time (MM:SS) return totals seconds since start of period."""
    try:
      # Format MM:SS
      minu, sec = clock_time.split(":")
    except:
      # Format SS.x
      minu = 0
      sec, _ = clock_time.split(".")
    minu = int(minu)
    sec = int(sec)
    return HockeyTime(period, minu * 60 + sec)


@attr.s(frozen=True)
class Game(object):
  away: str = attr.ib()
  home: str = attr.ib()
  # Date will be unspecified for predictions.
  date: Optional[Date] = attr.ib(default=None)

  def __str__(self):
    return f"{self.date}-{self.away}-{self.home}"


class Season(object):
  """Just stores an int representing a year.  """

  def __init__(self, year):
    self.year: int = year  # E.g. 2018 for the 2018-19 season.

  def get_all_dates(self) -> Iterable[Date]:
    """Returns all dates in a hockey season.

    May return additional dates, but does not return dates from other hockey
    seasons.
    """
    # Loops through October to Apr of next year.
    cursor = datetime.date(self.year, 10, 1)
    end_gate = datetime.date(self.year + 1, 4, 30)

    while cursor <= end_gate:
      yield cursor.year * 10000 + cursor.month * 100 + cursor.day
      cursor += datetime.timedelta(days=1)


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

    # Derived values
    self._away_att, self._home_att = None, None
    self._away_score, self._home_score = None, None
    self._winner, self._tie = None, False

    # Compute these values eagerly.  If you remove these lines, the derived
    #  values will get computed lazily.  But then these won't get saved to the
    #  file, so this work will get repeated with each new run.
    self._compute_atts()
    self._compute_scores()

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


@attr.s
class TrainTest(object):
  train: List[Game] = attr.ib()
  test: List[Game] = attr.ib()

  def __str__(self) -> str:
    CONCAT_LEN = 100

    result = list()
    result.append("Train:")
    train_string = ", ".join((str(game) for game in self.train))
    train_ell = "..." if len(train_string) > CONCAT_LEN else ""
    result.append(train_string[:CONCAT_LEN] + train_ell)
    result.append("Test:")
    test_string = ", ".join((str(game) for game in self.test))
    test_ell = "..." if len(test_string) > CONCAT_LEN else ""
    result.append(test_string[:CONCAT_LEN] + test_ell)
    return "\n".join(result)

  @staticmethod
  def from_games(cls, games: List[Game], test_portion: float = 0.2) -> 'TrainTest':
    """Make the last test_portion of games the test set - not random."""
    assert(0 < test_portion < 1.0)
    train_portion = 1.0 - test_portion
    cutoff = int(len(games) * train_portion)
    return TrainTest(train=games[:cutoff], test=games[cutoff:])
