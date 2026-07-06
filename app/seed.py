from .extensions import db
from .models import (
    Hotel,
    Offer,
    Restaurant,
)


def seed_demo_data():

    if Hotel.query.first():
        return

    hotels = [
        Hotel(
            slug="leela-palace-new-delhi",
            name="The Leela Palace New Delhi",
            city="New Delhi",
            state="Delhi",
            area="Chanakyapuri",
            stars=5,
            rating=4.8,
            reviews=3842,
            description=(
                "A refined luxury stay in the "
                "diplomatic heart of New Delhi."
            ),
        ),

        Hotel(
            slug="taj-lake-palace",
            name="Taj Lake Palace",
            city="Udaipur",
            state="Rajasthan",
            area="Lake Pichola",
            stars=5,
            rating=4.9,
            reviews=2210,
            description=(
                "An iconic palace hotel "
                "floating on Lake Pichola."
            ),
        ),

        Hotel(
            slug="alila-diwa-goa",
            name="Alila Diwa Goa",
            city="Goa",
            state="Goa",
            area="Majorda",
            stars=5,
            rating=4.7,
            reviews=1980,
            description=(
                "A serene luxury resort "
                "surrounded by South Goa landscapes."
            ),
        ),
    ]

    db.session.add_all(hotels)
    db.session.flush()

    offer_sets = [
        [
            ("Booking Partner A", 18200, 2000, 100),
            ("Booking Partner B", 17600, 1500, 0),
            ("Booking Partner C", 16900, 0, 0),
        ],
        [
            ("Booking Partner A", 31900, 3500, 0),
            ("Booking Partner B", 30500, 1800, 500),
            ("Booking Partner C", 29400, 0, 0),
        ],
        [
            ("Booking Partner A", 15700, 2500, 0),
            ("Booking Partner B", 14800, 1000, 200),
            ("Booking Partner C", 13900, 0, 0),
        ],
    ]

    for hotel, offers in zip(
        hotels,
        offer_sets
    ):
        for (
            provider,
            price,
            discount,
            cashback
        ) in offers:

            hotel.offers.append(
                Offer(
                    provider=provider,
                    listed_price=price,
                    discount=discount,
                    cashback=cashback,
                    cancellation="Free cancellation",
                    breakfast_included=True,
                )
            )

    restaurant_sets = [
        [
            (
                "Indian Accent",
                "Modern Indian",
                "Romantic",
                12,
                4.8,
                "₹₹₹₹",
            ),
            (
                "Bukhara",
                "North Indian",
                "Iconic",
                9,
                4.7,
                "₹₹₹₹",
            ),
            (
                "Diggin",
                "Cafe",
                "Casual",
                7,
                4.6,
                "₹₹",
            ),
        ],

        [
            (
                "Ambrai",
                "Rajasthani",
                "Romantic",
                10,
                4.7,
                "₹₹₹",
            ),
            (
                "Upre",
                "North Indian",
                "Rooftop",
                12,
                4.6,
                "₹₹₹",
            ),
        ],

        [
            (
                "Martin's Corner",
                "Goan",
                "Local favourite",
                9,
                4.6,
                "₹₹₹",
            ),
            (
                "The Fisherman's Wharf",
                "Seafood",
                "Dinner",
                14,
                4.5,
                "₹₹₹",
            ),
        ],
    ]

    for hotel, restaurants in zip(
        hotels,
        restaurant_sets
    ):
        for restaurant in restaurants:

            hotel.restaurants.append(
                Restaurant(
                    name=restaurant[0],
                    cuisine=restaurant[1],
                    occasion=restaurant[2],
                    travel_minutes=restaurant[3],
                    rating=restaurant[4],
                    price_level=restaurant[5],
                )
            )

    db.session.commit()
