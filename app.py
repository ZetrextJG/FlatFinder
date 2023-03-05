#!/bin/python3
import logging
import re
from typing import Generator, Optional

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

import config
from listings import Listing, OlxListing, OtodomListing
from db_connection import OffersDatabase
from offers import Offer, OfferBuilder

logging.basicConfig(level=logging.INFO)

def isFromOtodom(link: str) -> bool:
    return link.startswith("https://www.otodom") or link.startswith("https://otodom")


def isFromOlx(link: str) -> bool:
    return link.startswith("https://www.olx.pl/") or link.startswith("https://olx.pl")


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
        title: str = offerTag.find("h6").get_text()
        # Olx links lack the https prefix
        link: str = offerTag.get("href")
        if not link.startswith("https://"):
            link = "https://olx.pl" + link
        price_text: str = offerTag.find("p", {"data-testid": "ad-price"}).get_text()
        price = int(re.search(r"\d+", price_text.replace(" ", "")).group(0))

        listing = create_listing(title, price, link)
        if listing is not None:
            yield listing


def main():
    logging.info("Connecting to MongoDB")
    db = OffersDatabase()
    logging.info("Fetching offer listing from OLX")
    res = requests.get(config.SCRAPE_URL)
    logging.info("Extracting offers from downloaded HTML")
    soup = BeautifulSoup(res.content, "html.parser")
    for listing in extract_listings(soup):
        builder = OfferBuilder(listing)
        builder.addRent()
        builder.addBlacklisted()
        builder.addDistance()
        offer: Offer = builder.build()

        if offer.totalCost() < config.MAXIMUM_COST and not offer.isTooFar():
            if db.doesIdExists(offer._id): continue
            logging.info(f"Found new promissing offer: {offer.title}")
            __import__("pprint").pprint(offer.to_dict())
            logging.info(f"Uploading offer to DB: {offer.title}")
            db.insertOffer(offer)
            # logging.info(f"Sending emails with offer: {offer.title}")


if __name__ == "__main__":
    main()
