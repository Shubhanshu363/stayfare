from .base import HotelProvider
from .types import ProviderOffer


class MockBookingProvider(HotelProvider):

    name = "StayBook"

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
                "id": "sb-delhi-101",
                "name": "The Leela Palace New Delhi",
                "city": "New Delhi",
                "area": "Chanakyapuri",
                "price": 18200,
                "taxes": 1200,
                "discount": 2200,
                "cashback": 500,
                "rating": 4.8,
                "stars": 5,
            },
            {
                "id": "sb-udaipur-201",
                "name": "Taj Lake Palace",
                "city": "Udaipur",
                "area": "Lake Pichola",
                "price": 31900,
                "taxes": 2400,
                "discount": 3500,
                "cashback": 0,
                "rating": 4.9,
                "stars": 5,
            },
            {
                "id": "sb-goa-301",
                "name": "Alila Diwa Goa",
                "city": "Goa",
                "area": "Majorda",
                "price": 15700,
                "taxes": 1100,
                "discount": 2500,
                "cashback": 500,
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

            if destination_lower not in searchable:
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
                    room_name="Premier Room",
                    cancellation="Free cancellation",
                    breakfast_included=True,
                    rating=hotel["rating"],
                    stars=hotel["stars"],
                )
            )

        return results
