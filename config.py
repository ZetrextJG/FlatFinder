import re
from dotenv import load_dotenv
import os

from localization import Location

load_dotenv()

# Places that are too far away (not worth considering)
BLACKLIST = [
    "bemowo",
    "bemowie",
    "wilanow",
    "wilanowie",
    "ursus",
    "ursusie",
    "bielany",
    "bielanach",
    "wawer",
    "wawrze",
    "tarchomin",
    "tarchominie",
    "bialoleka",
    "bialolece",
    "brodno",
    "brodnie",
    "targowek",
    "targowku",
    "rembertow",
    "rembertowie",
    "goclaw",
    "goclawiu",
    "grodzisk",
    "grodzisku",
    "miedzylesie",
    "miedzylesiu",
]
# Latitude and Longitude of location to use a center (PW MINI)
CENTER_LOCATION = Location(52.222188, 21.007188)
# Maximum acceptable distance from center location in km
MAXIMUX_DISTANCE = 10  # km
# Maximum acceptable full cost
MAXIMUM_COST = 3500  # PLN
# Optimal search URL
# Takes care of basic price filtering
SCRAPE_URL = os.getenv("SCRAPE_URL")
STREET_REGEX = re.compile(
    r"(ul\.|ulicy|ulica|al\.|aleja|Ul\.|Ulica|Al\.|Aleja)\s*(([A-Z][a-z]+\s*))+"
)
