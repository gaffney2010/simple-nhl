import logging

logging.basicConfig(
    format="%(asctime)s  %(levelname)s:\t%(module)s::%(funcName)s:%(lineno)d\t-\t%(message)s",
    level=logging.INFO,
)

import seaborn as sns

sns.set_theme()

import game_data
import models
from shared_types import *


# Graph for Interaction model
data_18 = game_data.make_dataset(Season(2018))


# Shots on goal model
def get_shots_on_goal(game: Game) -> Optional[models.AwayHomeTarget]:
    """Gets scores for the game.  Default target."""
    data = game_data.load_game_data(game)
    if data is None:
        return None
    return (data.away_att, data.home_att)

for model in [
    models.InteractionModel(get_shots_on_goal),
    models.OffenseDefenseModel(get_shots_on_goal),
    models.OffenseOnlyModel(get_shots_on_goal)
]:
    logging.info(" ")
    logging.info("========================")
    logging.info(model)
    model.fit(data_18)
    logging.info(model.score(data_18))


# Goal percentage model
def goal_percentage(game: Game) -> Optional[models.AwayHomeTarget]:
    """Gets scores for the game.  Default target."""
    data = game_data.load_game_data(game)
    if data is None:
        return None
    if data.away_att == 0 or data.home_att == 0:
        return None
    return (data.away_score/data.away_att, data.home_score/data.home_att)

for model in [
    models.InteractionModel(goal_percentage),
    models.OffenseDefenseModel(goal_percentage),
    models.OffenseOnlyModel(goal_percentage),
    models.DefenseOnlyModel(goal_percentage)
]:
    logging.info(" ")
    logging.info("========================")
    logging.info(model)
    model.fit(data_18)
    logging.info(model.score(data_18))


# Combine shots with goal percentage to get a score model
class ShotsWithGoalPerc(models.PointsModel):
    """For this model, we have a variable for both the team and its opponent."""

    def __init__(self):
        # Average points per game for each team.
        self._shot_model = models.OffenseOnlyModel(get_shots_on_goal)
        self._goal_perc_model = models.DefenseOnlyModel(goal_percentage)
        super().__init__()

    def fit(self, train_set: List[Game]) -> None:
        self._shot_model.fit(train_set)
        self._goal_perc_model.fit(train_set)

    def predict(self, game: Game) -> models.AwayHomeTarget:
        away_att, home_att = self._shot_model.predict(game)
        away_perc, home_perc = self._goal_perc_model.predict(game)

        return (away_att * away_perc, home_att * home_perc)


logging.info("ShotsWithGoalPerc Model")
model = ShotsWithGoalPerc()
model.fit(data_18)
logging.info(model.score(data_18))
