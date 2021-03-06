"""Some constants that will be shared potentially across files."""

import os

# If downloading, you need to set this directory to equal the directory that
#  houses this file.
from computer_constants import TOP_LEVEL_DIR

# An allowlist of teams.  Should match to https://www.cbssports.com/nhl/teams/
#  short names in URLs.  We exclude Golden Knights in order to have
#  apples-to-apples comparison with earlier seasons.
ALL_TEAMS = [
    "CAR",
    "CHI",
    "CLB",
    "DAL",
    "DET",
    "FLA",
    "NSH",
    "TB",
    "BOS",
    "BUF",
    "NYI",
    "NYR",
    "NJ",
    "PHI",
    "PIT",
    "WAS",
    "CGY",
    "EDM",
    "MON",
    "OTT",
    "TOR",
    "VAN",
    "WPG",
    "ANA",
    "ARI",
    "COL",
    "LA",
    "MIN",
    "SJ",
    "STL",
    "LV",
]

DATA_DIR = os.path.join(TOP_LEVEL_DIR, "data")
LOGGING_DIR = os.path.join(TOP_LEVEL_DIR, "logging")
