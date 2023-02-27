#!/bin/python3
from unidecode import unidecode
from os import confstr
from bs4 import BeautifulSoup
from bs4.element import Tag
from pathlib import Path
import requests
import logging
import re
from localization import Location, StreetFinder
from datetime import datetime
from dataclasses import dataclass
from typing import Iterable, Optional, Set
import config

logging.basicConfig(encoding="utf-8", level=logging.DEBUG)


@dataclass
class Offer:
    title: str
    link: str
    price: int
    fetch_time: float

    description: str
    distance: Optional[float]
    backlisted: Optional[bool]
    rent: Optional[int]

    def totalCost(self) -> float:
        if not self.rent:
            return self.price
        return self.price + self.rent

    def isTooFar(self) -> bool:
        if self.backlisted: return True
        if self.distance is None: return False  # Cannot know for sure
        return self.distance <= config.MAXIMUX_DISTANCE


STREET_REGEX = re.compile(r"(ul\.|ulicy|ulica|al\.|aleja)\s*(([A-Z][a-z]+\s*))+")
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
        for blacklisted in config.BLACKLISTED_DISTRICTS:
            if blacklisted in self.wordsSet:
                return True
        return False

    def findHiddenRent(self) -> Optional[int]:
        for rent_word in ["czynsz", "czynszem", "czynszu"]:
            if rent_word in self.wordsSet:
                splited = self.descriptionParser.split(rent_word)
                match = re.search("\d+", splited[1])
                if match is None: continue
                probable_output = int(match.group())
                # Sanity check
                if probable_output < 0 or probable_output >= 2000: continue
                return probable_output
        return None

    def findPossibleLocation(self) -> Optional[Location]:
        match = re.search(STREET_REGEX, self.description)
        if not match: return None
        print("dsadfsadf")
        print(self.description)
        print(match)
        worded_location = match.group(2) # Group number based on regex
        finder = StreetFinder(city="Warszawa")
        return finder.findAverageLocation(worded_location)

@dataclass
class OfferListing:
    title: str
    link: str
    price: int
    size: float
    fetch_time: float

    def _extractRentFromOlx(self, soup: BeautifulSoup) -> Optional[int]:
        rent = None
        for liTag in soup.find_all("li"):
            text = liTag.get_text()
            if text.startswith("Czynsz"):
                rent = int(re.search(r"\d+", text).group(0))
        return rent

    def _handleOlxOffer(self, soup: BeautifulSoup) -> Offer:
        logging.debug(f"Processing OLX offer")
        descTag: Tag = soup.find("div", {"data-cy": "ad_description"})
        if descTag is None:
            logging.error(f"No description in listing: {self.title}")
            exit(4)
        desc = descTag.get_text()
        parser = DescriptionParser(self.title + " | " + desc)
        # Additional rent finder
        rentFromTable = self._extractRentFromOlx(soup)
        rentFromDesc = parser.findHiddenRent()
        rent = None
        if rentFromDesc is not None or rentFromTable is not None:
            if rentFromTable is None: rentFromTable = 0
            if rentFromDesc is None: rentFromDesc = 0
            rent = max(rentFromDesc, rentFromTable)
        # Blacklist check
        blacklisted = parser.doesContainBlacklisted()
        # Distance calculation
        distance = None
        if not blacklisted:
            location = parser.findPossibleLocation()
            if location:
                distance = location.distanceTo(config.GOAL_LOCATION)

        return Offer(self.title, self.link, self.price, self.fetch_time,
                     desc, distance, blacklisted, rent)

    def _isFromOtodom(self) -> bool:
        return (self.link.startswith("https://www.otodom") or
                self.link.startswith("https://otodom"))

    def _extractRentFromOtodom(self, soup: BeautifulSoup) -> Optional[int]:
        regex = re.compile(r'"key":"rent","value":"(\d+)"')
        script_data = " ".join(
            [script.get_text() for script in soup.find_all("script")]
        )
        match = re.search(regex, script_data)
        if match is None: 
            return None
        return int(match.group(1))

    def _handleOtodomOffer(self, soup: BeautifulSoup) -> Offer:
        logging.debug(f"Processing Otodom offer")
        descTag: Tag = soup.find("div", {"data-cy": "adPageAdDescription"})
        if descTag is None:
            logging.error(f"No description in listing: {self.title}")
            exit(4)

        desc = descTag.get_text()
        parser = DescriptionParser(self.title + " | " + desc)
        rentFromTable = self._extractRentFromOtodom(soup)
        rentFromDesc = parser.findHiddenRent()
        rent = None
        if rentFromDesc is not None or rentFromTable is not None:
            if rentFromTable is None: rentFromTable = 0
            if rentFromDesc is None: rentFromDesc = 0
            rent = max(rentFromDesc, rentFromTable)
        # Blacklist check
        blacklisted = parser.doesContainBlacklisted()
        # Distance calculation
        distance = None
        if not blacklisted:
            location = parser.findPossibleLocation()
            if location:
                distance = location.distanceTo(config.GOAL_LOCATION)

        return Offer(self.title, self.link, self.price, self.fetch_time,
                     desc, distance, blacklisted, rent)


    def buildOffer(self) -> Offer:
        logging.debug(f"Starting build process for listing: {self.title}")
        logging.debug("Fetching listing link")
        offer_res = requests.get(self.link)
        if offer_res.status_code != 200:
            logging.error("Failed to make HTML request")
            exit(3)
        html_content = offer_res.content
        soup = BeautifulSoup(html_content, "html.parser")
        if self._isFromOtodom():
            logging.debug(f"Found Otodom offer: ")
            return self._handleOtodomOffer(soup)
        logging.debug(f"Found OLX offer")
        return self._handleOlxOffer(soup)


def extract_offers(listings_html: str) -> Iterable[OfferListing]:
    soup = BeautifulSoup(listings_html, "html.parser")
    found_offers = soup.find_all("div", {"data-cy": "l-card"})
    parsed_offers = []
    for offerTag in found_offers:
        offerTag: Tag = found_offers.pop().find("a")
        title: str = offerTag.find(
            "h6"
        ).get_text()  # We can use this later to create an id (maybe with price as salt to monitor changes)
        link: str = offerTag.get("href")
        if not link.startswith("https://"):
            link = "https://olx.pl" + link
        price_text: str = offerTag.find("p", {"data-testid": "ad-price"}).get_text()
        price = int(re.search(r"\d+", price_text.replace(" ", "")).group(0))
        # creation_info: str = offer.find("p", {"data-testid": "location-date"}).get_text()
        sizeWrapper = offerTag.find("div", {"color": "text-global-secondary"})
        size = int(re.search(r"\d+", sizeWrapper.get_text()).group(0))
        fetch_time = datetime.now().timestamp
        offerListing = OfferListing(title, link, price, size, fetch_time)
        parsed_offers.append(offerListing)
    return parsed_offers


def main():
    logging.debug("Fetching offer listing from OLX")
    res = requests.get(config.FETCH_URL)
    logging.debug("Extracting offers from downloaded HTML")
    listings = extract_offers(res.content)
    for offerListing in listings:
        # offerListing.title # use this to create hash for objects
        # offerListing.price
        offer = offerListing.buildOffer()
        print("-----")
        print(offer.title)
        print(offer.totalCost())
        print(offer.isTooFar())
        print("-----")

if __name__ == "__main__":
    main()
