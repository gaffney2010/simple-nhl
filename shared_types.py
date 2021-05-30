"""Includes some shared types.

Unlike other files, we will import as "from shared_types import *".
"""

import datetime
from typing import Iterable, List

import attr

Date = int  # YYYYMMDD
Team = str
GameData = str

@attr.s
class Game(object):
  home: str = attr.ib()
  away: str = attr.ib()
  home_score: int = attr.ib(default=0)
  away_score: int = attr.ib(default=0)

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
class TrainTest(object):
  train: List[Game] = attr.ib()
  test: List[Game] = attr.ib()

  @staticmethod
  def from_games(cls, games: List[Game], test_portion: float = 0.2) -> 'TrainTest':
    """Make the last test_portion of games the test set - not random."""
    assert(0 < test_portion < 1.0)
    train_portion = 1.0 - test_portion
    cutoff = int(len(games) * train_portion)
    return TrainTest(train=games[:cutoff], test=games[cutoff:])