from unidecode import unidecode
import re
from typing import Optional, Set
import config
from localization import Location, StreetFinder

class DescriptionParser:
    description: str
    wordsSet: Set[str]

    def __init__(self, description: str) -> None:
        # Make one line and trim excesive whitespaces
        description = description.replace("\n", " ")
        description = re.sub(r"\s+", " ", description)
        description = unidecode(description)
        self.description = description
        description = description.lower()
        description = re.sub(r"[,\.\!]+", "", description)
        self.descriptionParser = description
        self.wordsSet = set(description.split(" "))

    def doesContainBlacklisted(self) -> bool:
        for blacklisted in config.BLACKLIST:
            if blacklisted in self.wordsSet:
                return True
        return False

    def findHiddenRent(self) -> Optional[float]:
        for rent_word in ["czynsz", "czynszem", "czynszu"]:
            if rent_word in self.wordsSet:
                splited = self.descriptionParser.split(rent_word)
                match = re.search("\d+", splited[1])
                if match is None: continue
                probable_output = float(match.group())
                # Sanity check
                if probable_output >= 0 and probable_output < 2000: 
                    return probable_output

        match = re.search("plus\s*(\d+)\s*", self.description.lower())
        if match is not None:
            probable_output = float(match.group(1))
            if probable_output >= 0 and probable_output < 2000: 
                return probable_output
        
        return None

    def findPossibleLocation(self) -> Optional[Location]:
        match = re.search(config.STREET_REGEX, self.description)
        if not match: return None
        worded_location = match.group(2) # Group number based on regex
        finder = StreetFinder(city="Warszawa")
        return finder.findAverageLocation(worded_location)
