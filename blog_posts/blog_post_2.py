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
    models.InteractionModel(),
    models.OffenseDefenseModel(),
    models.OffenseOnlyModel()
]:
    logging.info(" ")
    logging.info("========================")
    logging.info(model)
    model.fit(data_18)
    logging.info(model.score(data_18))
