#!/bin/python3
from bs4 import BeautifulSoup
from bs4.element import Tag
import requests
import logging
import re
from listings import Listing, OlxListing, OtodomListing
from typing import Optional, Generator
import config
from offers import OfferBuilder

logging.basicConfig(level=logging.WARN)

def isFromOtodom(link: str) -> bool:
    return (link.startswith("https://www.otodom") or
            link.startswith("https://otodom"))

def isFromOlx(link: str) -> bool:
    return (link.startswith("https://www.olx.pl/") or
            link.startswith("https://olx.pl"))


def create_listing(title: str, price: float, link: str) -> Optional[Listing]:
    if isFromOlx(link):
        return OlxListing(title, price, link)
    elif isFromOtodom(link):
        return OtodomListing(title, price, link)
    else:
        logging.warning(f"Unknown listing portal at url: {link}")
        return None

def extract_listings(listings_crawler: BeautifulSoup) -> Generator[Listing, None, None]:
    found_listings = listings_crawler.find_all("div", {"data-cy": "l-card"})
    for offerTag in found_listings:
        offerTag: Tag = found_listings.pop().find("a")
        title: str = offerTag.find(
            "h6"
        ).get_text()
        # Olx links lack the https prefix
        link: str = offerTag.get("href")
        if not link.startswith("https://"):
            link = "https://olx.pl" + link
        price_text: str = offerTag.find(
            "p", {"data-testid": "ad-price"}
        ).get_text()
        price = int(re.search(r"\d+", price_text.replace(" ", "")).group(0))

        listing = create_listing(title, price, link)
        if listing is not None:
            yield listing


def main():
    logging.debug("Fetching offer listing from OLX")
    res = requests.get(config.SCRAPE_URL)
    logging.debug("Extracting offers from downloaded HTML")
    soup = BeautifulSoup(res.content, "html.parser")
    for listing in extract_listings(soup):
        builder = OfferBuilder(listing)
        builder.addRent()
        builder.addBlacklisted()
        builder.addDistance()
        offer = builder.build()

        if offer.totalCost() < config.MAXIMUM_COST and not offer.isTooFar():
            __import__('pprint').pprint(offer.to_dict())

if __name__ == "__main__":
    main()
