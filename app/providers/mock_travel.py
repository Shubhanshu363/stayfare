from .base import HotelProvider
from .types import ProviderOffer


class MockTravelProvider(HotelProvider):

    name = "TripNest"

    def search(
        self,
        destination,
        check_in=None,
        check_out=None,
        adults=2,
        rooms=1,
    ):
        destination_lower = (
            destination.lower().strip()
        )

        inventory = [
            {
                "id": "tn-8821",
                "name": "Leela Palace New Delhi",
                "city": "Delhi",
                "area": "Chanakya Puri",
                "price": 17600,
                "taxes": 1500,
                "discount": 1800,
                "cashback": 900,
                "rating": 4.8,
                "stars": 5,
            },
            {
                "id": "tn-7732",
                "name": "Taj Lake Palace Udaipur",
                "city": "Udaipur",
                "area": "Pichola",
                "price": 30500,
                "taxes": 2600,
                "discount": 1800,
                "cashback": 1200,
                "rating": 4.9,
                "stars": 5,
            },
            {
                "id": "tn-6643",
                "name": "Alila Diwa",
                "city": "South Goa",
                "area": "Majorda",
                "price": 14800,
                "taxes": 1300,
                "discount": 1000,
                "cashback": 700,
                "rating": 4.7,
                "stars": 5,
            },
        ]

        aliases = {
            "new delhi": "delhi",
            "south goa": "goa",
        }

        normalized_destination = aliases.get(
            destination_lower,
            destination_lower,
        )

        results = []

        for hotel in inventory:

            searchable = " ".join(
                [
                    hotel["name"],
                    hotel["city"],
                    hotel["area"],
                ]
            ).lower()

            if (
                normalized_destination
                not in searchable
            ):
                continue

            results.append(
                ProviderOffer(
                    provider=self.name,
                    provider_hotel_id=hotel["id"],
                    hotel_name=hotel["name"],
                    city=hotel["city"],
                    area=hotel["area"],
                    listed_price=hotel["price"],
                    taxes=hotel["taxes"],
                    discount=hotel["discount"],
                    cashback=hotel["cashback"],
                    room_name="Luxury King Room",
                    cancellation="Free cancellation until 24 hours before stay",
                    breakfast_included=False,
                    rating=hotel["rating"],
                    stars=hotel["stars"],
                )
            )

        return results
