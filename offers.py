import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from dataclasses_json import dataclass_json

import config
from listings import Listing
from parsers import DescriptionParser


@dataclass_json
@dataclass
class Offer:
    _id: str = field(init=False)
    title: str
    link: str
    price: int
    createdAt: datetime

    description: str
    distance: Optional[float]
    backlisted: Optional[bool]
    rent: Optional[int]

    def __post_init__(self) -> None:
        self._id = hash(f"{self.title} | {self.price}")

    def totalCost(self) -> float:
        if not self.rent:
            return self.price
        return self.price + self.rent

    def isTooFar(self) -> bool:
        if self.backlisted:
            return True
        if self.distance is None:
            return False  # Cannot know for sure
        return self.distance <= config.MAXIMUX_DISTANCE


@dataclass
class OfferBuilder:
    listing: Listing
    createdAt: datetime

    description: Optional[str]
    distance: Optional[float]
    backlisted: Optional[bool]
    rent: Optional[int]

    def __init__(self, listing: Listing) -> None:
        logging.debug(f"Starting build process for listing: {listing.title}")
        self.listing = listing

        self.createdAt = datetime.now()
        self.listing = listing
        self.description = self.listing.getDescription()
        prefixedDescription = self.listing.title + " | " + self.description
        self.parser = DescriptionParser(prefixedDescription)

        self.distance = None
        self.backlisted = None
        self.rent = None

    def addRent(self) -> None:
        logging.debug(f"Calculating rent for: {self.listing.title}")
        displayedRent = self.listing.getDisplayedRent()
        hiddenRent = self.parser.findHiddenRent()
        if hiddenRent is not None or displayedRent is not None:
            if displayedRent is None:
                displayedRent = 0
            if hiddenRent is None:
                hiddenRent = 0
            self.rent = max(hiddenRent, displayedRent)

    def addBlacklisted(self) -> None:
        logging.debug(f"Checking for blaclisted words for: {self.listing.title}")
        self.backlisted = self.parser.doesContainBlacklisted()

    def addDistance(self) -> None:
        logging.debug(f"Calculating probable distance for: {self.listing.title}")
        if self.backlisted is True:
            return None
        location = self.parser.findPossibleLocation()
        if location is not None:
            self.distance = location.distanceTo(config.CENTER_LOCATION)

    def build(self) -> Offer:
        logging.debug(f"Creating offer object for: {self.listing.title}")
        return Offer(
            self.listing.title,
            self.listing.link,
            self.listing.price,
            self.createdAt,
            self.description,
            self.distance,
            self.backlisted,
            self.rent,
        )
