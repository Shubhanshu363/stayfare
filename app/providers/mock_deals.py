from .base import HotelProvider
from .types import ProviderOffer


class MockDealsProvider(HotelProvider):

    name = "RoomRush"

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
                "id": "rr-1101",
                "name": "The Leela Palace",
                "city": "New Delhi",
                "area": "Chanakyapuri",
                "price": 16900,
                "taxes": 1800,
                "discount": 0,
                "cashback": 1500,
                "rating": 4.8,
                "stars": 5,
            },
            {
                "id": "rr-2202",
                "name": "Taj Lake Palace",
                "city": "Udaipur",
                "area": "Lake Pichola",
                "price": 29400,
                "taxes": 2900,
                "discount": 0,
                "cashback": 800,
                "rating": 4.9,
                "stars": 5,
            },
            {
                "id": "rr-3303",
                "name": "Alila Diwa Goa Resort",
                "city": "Goa",
                "area": "Majorda",
                "price": 13900,
                "taxes": 1700,
                "discount": 0,
                "cashback": 1000,
                "rating": 4.7,
                "stars": 5,
            },
        ]

        results = []

        for hotel in inventory:

            searchable = " ".join(
                [
                    hotel["name"],
                    hotel["city"],
                    hotel["area"],
                ]
            ).lower()

            city_match = (
                destination_lower in searchable
            )

            if (
                destination_lower == "delhi"
                and "new delhi" in searchable
            ):
                city_match = True

            if not city_match:
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
                    room_name="Best Available Room",
                    cancellation="Non-refundable",
                    breakfast_included=True,
                    rating=hotel["rating"],
                    stars=hotel["stars"],
                )
            )

        return results
