#!/bin/python3
from bs4 import BeautifulSoup
from bs4.element import Tag
from pathlib import Path
import requests
import re
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
import config


@dataclass
class Offer:
    title: str
    link: str
    description: str
    price: int 
    rent: Optional[int]

    def totalCost(self) -> float:
        if not self.rent: return self.price
        return self.price + self.rent


def extract_description_olx(offer_html: Path):
    soup = BeautifulSoup(offer_html, "html.parser")
    res_set = soup.find_all("div", {"data-cy": "ad_description"})
    if len(res_set) == 0: return ""
    desc: Tag = res_set.pop()
    return desc.get_text()


def extract_offers(listings_html: str):
    soup = BeautifulSoup(listings_html, "html.parser")
    found_offers = soup.find_all("div", {"data-cy": "l-card"})
    parsed_offers = []
    for offer in found_offers:
        offer: Tag = found_offers.pop().find("a")
        title: str = offer.find("h6").get_text() # We can use this later to create an id (maybe with price as salt to monitor changes)
        link: str = offer.get("href")
        if not link.startswith("https://"):
            link = "https://olx.pl" + link
        price_text: str = offer.find("p", {"data-testid": "ad-price"}).get_text()
        price = int(re.search(r"\d+", price_text.replace(" ", "")).group(0))
        # creation_info: str = offer.find("p", {"data-testid": "location-date"}).get_text()
        fetch_time = datetime.now().timestamp
        parsed_offers.append({"title": title, "link": link, "price": price, "fetch_time": fetch_time})
    return parsed_offers 


def main():
    res = requests.get(config.FETCH_URL)
    print(extract_offers(res.text))


if __name__ == "__main__":
    main()
