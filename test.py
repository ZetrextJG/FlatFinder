from typing import Optional
import requests
from dataclasses import dataclass
import numpy as np
import haversine as hs

@dataclass
class Location:
    longitude: float # W or E
    latitude: float # N or S

    def distanceTo(self, other: "Location") -> float:
        loc1 = (self.latitude, self.longitude)
        loc2 = (other.latitude, other.longitude)
        return hs.haversine(loc1, loc2)


MINI_PW = Location(52.222188, 21.007188)

class StreetFinder:
    API_URL: str = "https://capap.gugik.gov.pl/api/fts/gc/pkt"
    city: str

    def __init__(self, city: str = "Warszawa") -> None:
        self.city = city

    def createRequestJSON(self, street: str) -> dict:
        return {
            "reqs": [
                {
                    "ul_pelna": street,
                    "miejsc_nazwa": self.city
                }
            ],
            "useExtServiceIfNotFound": True
        }

    def fetchPointsCoordiantes(self, street: str) -> Optional[np.ndarray]:
        res = requests.post(
            StreetFinder.API_URL,
            json = self.createRequestJSON(street)
        )
        if res.status_code != 200: return None
        content = res.json()
        if len(content) == 0 or "others" not in content[0]: return None
        places = content[0]["others"]
        found_coords = []
        for place in places:
            coord = place["geometry"]["coordinates"]
            found_coords.append(coord)
        return np.asarray(found_coords)
    
    def findAverageLocation(self, street: str) -> Optional[Location]:
        coordinates = self.fetchPointsCoordiantes(street)
        if coordinates is None: return None
        avg = coordinates.mean(axis=0)
        return Location(avg[1], avg[0])



