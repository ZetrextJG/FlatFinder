from abc import ABC, abstractmethod
import logging
from bs4 import BeautifulSoup
import requests
from typing import Optional
import re
from bs4.element import Tag

class Listing(ABC):
    title: str
    price: float
    link: str

    @abstractmethod
    def getDisplayedRent(self) -> Optional[float]:
        pass

    @abstractmethod
    def getDescription(self) -> str:
        pass
    
    def createCrawler(self) -> BeautifulSoup:
        logging.debug(f"Fetching link confent for: {self.title}")
        offer_res = requests.get(self.link)
        if offer_res.status_code != 200:
            raise Exception("Failed to make HTML request")
        html_content = offer_res.content
        logging.debug(f"Creaing soup object for: {self.title}")
        return BeautifulSoup(html_content, "html.parser")


class OlxListing(Listing):
    title: str
    price: float
    link: str
    crawler: BeautifulSoup

    def __init__(self, title: str, price: float, link: str) -> None:
        self.title = title
        self.price = price
        self.link = link

        self.crawler = self.createCrawler()

    def getDisplayedRent(self) -> Optional[float]:
        logging.debug(f"Searching for displayed rent in: {self.title}")
        rent = None
        for liTag in self.crawler.find_all("li"):
            text = liTag.get_text()
            if text.startswith("Czynsz"):
                rent = int(re.search(r"\d+", text).group(0))
        return rent

    def getDescription(self) -> str:
        logging.debug(f"Searching for description in: {self.title}")
        descTag: Tag = self.crawler.find(
            "div", 
            {"data-cy": "ad_description"}
        )
        if descTag is None:
            raise Exception(f"No description in listing: {self.title}")
        return descTag.get_text()


class OtodomListing(Listing):
    title: str
    price: float
    link: str
    crawler: BeautifulSoup

    def __init__(self, title: str, price: float, link: str) -> None:
        self.title = title
        self.price = price
        self.link = link

        self.crawler = self.createCrawler()

    def getDisplayedRent(self) -> Optional[float]:
        logging.debug(f"Searching for displayed rent in: {self.title}")
        regex = re.compile(r'"key":"rent","value":"(\d+)"')
        script_data = " ".join(
            [script.get_text() for script in 
                self.crawler.find_all("script")]
        )
        match = re.search(regex, script_data)
        if match is None: 
            return None
        return int(match.group(1))

    def getDescription(self) -> str:
        logging.debug(f"Searching for description in: {self.title}")
        descTag: Tag = self.crawler.find(
            "div", 
            {"data-cy": "adPageAdDescription"}
        )
        if descTag is None:
            raise Exception(f"No description in listing: {self.title}")
        return descTag.get_text()

