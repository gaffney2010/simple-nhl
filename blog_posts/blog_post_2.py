import logging

logging.basicConfig(
    format="%(asctime)s  %(levelname)s:\t%(module)s::%(funcName)s:%(lineno)d\t-\t%(message)s",
    level=logging.INFO,
)

import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm

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
    return (data.away_score / data.away_att, data.home_score / data.home_att)


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

    def fit(self, train_set: TrainTest) -> None:
        self._shot_model.fit(train_set)
        self._goal_perc_model.fit(train_set)

    def predict(self, game: Game) -> models.AwayHomeTarget:
        away_att, home_att = self._shot_model.predict(game)
        away_perc, home_perc = self._goal_perc_model.predict(game)

        return (away_att * away_perc, home_att * home_perc)


logging.info("ShotsWithGoalPerc Model")
shots_w_gp = ShotsWithGoalPerc()
shots_w_gp.fit(data_18)
logging.info(shots_w_gp.score(data_18))

logging.info("")
logging.info("")

benchmark = models.OffenseOnlyModel()
benchmark.fit(data_18)

rando = models.RandomModel()
rando.fit(data_18)


for model in (rando, benchmark, shots_w_gp):
    logging.info("===================")
    logging.info(model)

    score_diff, away_won, neg_home_ad = list(), list(), list()
    for game in data_18.train:
        data = game_data.load_game_data(game)
        if data.away_score == data.home_score:
            # Tie.  Should never happen?
            continue

        pred_away, pred_home = model.predict(game)
        score_diff.append(pred_away - pred_home)
        away_won.append(data.away_score > data.home_score)  # Actual
        neg_home_ad.append(1)
    df = pd.DataFrame({"away_won": away_won, "score_diff": score_diff,
                       "neg_home_ad": neg_home_ad})
    log_reg_ = sm.Logit(df["away_won"], df[["score_diff", "neg_home_ad"]])
    log_reg = log_reg_.fit()
    # logging.info(results.summary())

    logging.info("")

    # Calculate the win percentage - how often the model is right.
    win_num, win_den = 0, 0
    # Calculate the log-likelihood.
    log_likelihood = 0.0

    for game in data_18.test:
        # String the two predictions together
        data = game_data.load_game_data(game)
        if data.away_score == data.home_score:
            # Tie.  Should never happen?
            continue

        pred_away, pred_home = model.predict(game)
        pred = log_reg.predict([pred_away - pred_home, 1])[0]
        act = data.away_score > data.home_score

        win_den += 1
        if (pred > 0.5 and act) or (pred < 0.5 and not act):
            win_num += 1

        if act:
            log_likelihood += np.log(pred)
        else:
            log_likelihood += np.log(1 - pred)

    logging.info("# pts")
    logging.info(win_den)
    logging.info("Win perc")
    logging.info(win_num / win_den)
    logging.info("Log-likelihood")
    logging.info(log_likelihood)
