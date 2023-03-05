import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from offers import Offer

load_dotenv()
MONGO_URL = os.getenv("MONGO_URL")


class OffersDatabase:
    cluster: MongoClient
    db: Database
    collection: Collection

    def __init__(self) -> None:
        self.cluster = MongoClient(MONGO_URL)
        self.db = self.cluster["main"]
        self.collection = self.db["offers"]

    def doesIdExists(self, id: int) -> bool:
        return self.collection.count_documents({"_id": id}) > 0

    def insertOffer(self, offer: Offer) -> None:
        self.collection.insert_one(offer.to_dict())
