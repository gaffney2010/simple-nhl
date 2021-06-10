import logging

logging.basicConfig(
    format="%(asctime)s  %(levelname)s:\t%(module)s::%(funcName)s:%(lineno)d\t-\t%(message)s",
    level=logging.INFO,
)

import numpy as np

import seaborn as sns

sns.set_theme()

from constants import *
import game_data
import models
from shared_types import *


def plot_table(model: models.PointsModel) -> None:
    cells = list()
    for team in ALL_TEAMS:
        new_row = list()
        for opp in ALL_TEAMS:
            if opp == team:
                new_row.append(np.nan)
            else:
                game = Game(home=team, away=opp)
                new_row.append(model.predict(game)[0])
        cells.append(new_row)

    sns.heatmap(cells, xticklabels=ALL_TEAMS, yticklabels=ALL_TEAMS)

# Graph for Interaction model
data_18 = game_data.make_dataset(Season(2018))
logging.debug(str(data_18))

model = models.InteractionModel()
for model in [
    models.InteractionModel(),
    models.OffenseDefenseModel(),
    models.OffenseOnlyModel()
]:
    logging.info(" ")
    logging.info("========================")
    model.fit(data_18)
    logging.info(model.score(data_18))
    # plot_table(model1)
