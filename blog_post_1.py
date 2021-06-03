import numpy as np

import seaborn as sns; sns.set_theme()

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
print(str(data_18))
model1 = models.InteractionModel()
model1.fit(data_18)
plot_table(model1)


# Graph for Offense-Defense model
model2 = models.OffenseDefenseModel()
model2.fit(data_18)
plot_table(model2)


# Graph for Offense-Only model
model3 = models.OffenseOnlyModel()
model3.fit(data_18)
plot_table(model3)


# Compute score across 5 years ending in 2018
for model in (model1, model2, model3):
  avg_score = 0
  for year in range(2014, 2019):
    ds = game_data.make_dataset(Season(year))
    model.fit(ds)
    avg_score += model.score(ds)
  avg_score /= 5
  print("==========")
  print(model)
  print(avg_score)
