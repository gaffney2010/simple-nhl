from collections import defaultdict
from typing import Tuple

import pandas as pd
import statsmodel as sm

from constants import *
from shared_types import *


class PointsModel(object):
  """A Model class contains information for training and predicting."""

  def __init__(self):
    pass

  def fit_impl(self, train_set: List[Game]) -> None:
    """Implement this in a child class."""
    raise NotImplementedError

  def fit(self, train_test: TrainTest) -> None:
    """Fits internal variables (by year) from the passed dataset."""
    self.fit_impl(train_test.train)

  def predict(self, game: Game) -> Tuple[float, float]:
    """Returns the expected points for the home and away teams (resp.).
    Implement in the child class."""
    raise NotImplementedError

  def score(self, train_test: TrainTest) -> float:
    """Computes the MSE on the test set of the train_test passed."""
    num, den = 0, 0
    for game in train_test.test:
      if game.home not in ALL_TEAMS or game.away not in ALL_TEAMS:
        # We skip Golden Knights so that code can run the same for all years
        continue

      act_home_pts, act_away_pts = game.home_score, game.away_score
      pred_home_pts, pred_away_pts = self.predict(game)

      if pred_home_pts != pred_home_pts or pred_away_pts != pred_away_pts:
        # Models may return nan for unknowns.
        continue

      num += (act_home_pts - pred_home_pts) ** 2
      num += (act_away_pts - pred_away_pts) ** 2
      den += 2
    return num / den


class InteractionModel(PointsModel):
  """For this model, the prediction of win margin is average win margin from the
  previous times the two teams met."""

  def __init__(self):
    # For (x, y), the average points x won when playing against y.
    self._avg_pts = dict()
    super().__init__()

  def fit_impl(self, train_set: List[Game]) -> None:
    _points_won = defaultdict(int)
    _played = defaultdict(int)

    for game in train_set:
      _points_won[(game.home, game.away)] += game.home_score
      _points_won[(game.away, game.home)] += game.away_score
      _played[(game.home, game.away)] += 1
      _played[(game.away, game.home)] += 1

    for k in _played.keys():
      self._avg_pts[k] = _points_won[k] / _played[k]

  def predict(self, game: Game) -> Tuple[float, float]:
    assert (self._avg_pts)  # fit has already run
    home_pred = self._avg_pts.get((game.home, game.away), np.nan)
    away_pred = self._avg_pts.get((game.away, game.home), np.nan)
    return home_pred, away_pred


class OffenseDefenseModel(PointsModel):
  """For this model, we have a variable for both the team and its opponent."""

  def __init__(self):
    # The number of points expected to score against base team.
    self._points_for = dict()
    # For each team, t, how many points fewer a team is expected to score
    #  playing t than if they had played the base team.
    self._points_against = dict()
    super().__init__()

  def fit_impl(self, train_set: List[Game]) -> None:
    data = list()
    for game in train_set:
      data.append(
        {"team": game.home, "opp": game.away, "points": game.home_score})
      data.append(
        {"team": game.away, "opp": game.home, "points": game.away_score})

    points_df = pd.DataFrame(data)

    points_x = pd.concat(
      [pd.get_dummies(points_df["team"], prefix="TEAM"),
       pd.get_dummies(points_df["opp"], prefix="OPP", drop_first=True)],
      axis=1)

    model = sm.OLS(points_df["points"], points_x)
    results = model.fit()

    for team in ALL_TEAMS:
      self._points_for[team] = results.params.get(f"TEAM_{team}")
      self._points_against[team] = results.params.get(f"OPP_{team}", 0)

  def predict(self, game: Game) -> Tuple[float, float]:
    assert (self._points_for)  # fit has already run
    return (self._points_for[game.home] - self._points_against[game.away],
            self._points_for[game.away] - self._points_against[game.home])


class OffenseOnlyModel(PointsModel):
  """For this model, we have a variable for both the team and its opponent."""

  def __init__(self):
    # Average points per game for each team.
    self._avg_pts = dict()
    super().__init__()

  def fit_impl(self, train_set: List[Game]) -> None:
    _points_won = defaultdict(int)
    _played = defaultdict(int)

    for game in train_set:
      _points_won[game.home] += game.home_score
      _points_won[game.away] += game.away_score
      _played[game.home] += 1
      _played[game.away] += 1

    for k in _played.keys():
      self._avg_pts[k] = _points_won[k] / _played[k]

  def predict(self, game: Game) -> Tuple[float, float]:
    assert(self._avg_pts)  # fit has already run
    return self._avg_pts[game.home], self._avg_pts[game.away]