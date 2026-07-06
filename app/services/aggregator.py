from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)

from flask import current_app, has_app_context

from app.models import Hotel
from app.providers.types import ProviderOffer

from app.providers.booking import BookingProvider
from app.providers.mock_booking import (
    MockBookingProvider,
)
from app.providers.mock_travel import (
    MockTravelProvider,
)
from app.providers.mock_deals import (
    MockDealsProvider,
)

from .hotel_matcher import (
    offers_match,
    name_similarity,
    normalize_city,
)


PROVIDERS = [
    MockBookingProvider(),
    MockTravelProvider(),
    MockDealsProvider(),
]


def get_providers():
    providers = list(PROVIDERS)

    if has_app_context():
        mode = str(current_app.config.get("PROVIDER_MODE", "DEMO")).upper()
        if mode in {"LIVE", "DEGRADED"}:
            providers.append(
                BookingProvider(
                    api_key=current_app.config.get("BOOKING_API_TOKEN"),
                    base_url=current_app.config.get("BOOKING_API_BASE_URL"),
                    affiliate_id=current_app.config.get("BOOKING_AFFILIATE_ID"),
                    timeout=current_app.config.get("BOOKING_API_TIMEOUT_SECONDS"),
                )
            )

    return providers


class AggregatedOffer(ProviderOffer):
    def __init__(
        self,
        offer,
        offer_id=None,
        hotel_id=None,
        hotel=None,
    ):
        super().__init__(
            provider=offer.provider,
            provider_hotel_id=offer.provider_hotel_id,
            hotel_name=offer.hotel_name,
            city=offer.city,
            area=offer.area,
            listed_price=offer.listed_price,
            taxes=offer.taxes,
            discount=offer.discount,
            cashback=offer.cashback,
            room_name=offer.room_name,
            cancellation=offer.cancellation,
            breakfast_included=offer.breakfast_included,
            affiliate_url=offer.affiliate_url,
            rating=offer.rating,
            stars=offer.stars,
            metadata=offer.metadata,
        )
        self.id = offer_id
        self.hotel_id = hotel_id
        self.hotel = hotel


def search_provider(
    provider,
    destination,
    check_in,
    check_out,
    adults,
    rooms,
):
    return provider.search(
        destination=destination,
        check_in=check_in,
        check_out=check_out,
        adults=adults,
        rooms=rooms,
    )


def find_database_hotel(
    representative,
):
    hotels = Hotel.query.all()

    best_match = None
    best_score = 0.0

    provider_city = normalize_city(
        representative.city
    )

    for hotel in hotels:

        database_city = normalize_city(
            hotel.city
        )

        if (
            database_city
            != provider_city
        ):
            continue

        score = name_similarity(
            representative.hotel_name,
            hotel.name,
        )

        if score > best_score:
            best_score = score
            best_match = hotel

    if best_score >= 0.60:
        return best_match

    return None


def aggregate_search(
    destination,
    check_in=None,
    check_out=None,
    adults=2,
    rooms=1,
):
    all_offers = []
    provider_errors = []

    providers = get_providers()
    provider_mode = str(current_app.config.get("PROVIDER_MODE", "DEMO")).upper()

    with ThreadPoolExecutor(
        max_workers=len(providers)
    ) as executor:

        future_map = {
            executor.submit(
                search_provider,
                provider,
                destination,
                check_in,
                check_out,
                adults,
                rooms,
            ): provider
            for provider in providers
        }

        for future in as_completed(
            future_map
        ):
            provider = future_map[future]

            try:
                offers = future.result()

                all_offers.extend(
                    offers
                )

            except Exception as error:
                provider_errors.append(
                    {
                        "provider": provider.name,
                        "error": str(error),
                    }
                )

    if provider_errors:
        provider_mode = "DEGRADED"

    groups = []

    for offer in all_offers:

        matched_group = None

        for group in groups:

            if offers_match(
                offer,
                group["representative"],
            ):
                matched_group = group
                break

        if matched_group:

            matched_group[
                "offers"
            ].append(offer)

        else:

            groups.append(
                {
                    "representative": offer,
                    "offers": [offer],
                }
            )

    results = []

    for group in groups:

        ranked_offers = sorted(
            group["offers"],
            key=lambda item:
            item.effective_price,
        )

        best = ranked_offers[0]

        database_hotel = (
            find_database_hotel(
                group["representative"]
            )
        )

        normalized_offers = [
            AggregatedOffer(
                offer,
                offer_id=(
                    f"{offer.provider}|"
                    f"{database_hotel.id if database_hotel else ''}|"
                    f"{database_hotel.slug if database_hotel else ''}|"
                    f"{offer.provider_hotel_id}"
                ),
                hotel_id=(
                    database_hotel.id
                    if database_hotel
                    else None
                ),
                hotel=database_hotel,
            )
            for offer in ranked_offers
        ]

        results.append(
            {
                "name": (
                    database_hotel.name
                    if database_hotel
                    else group[
                        "representative"
                    ].hotel_name
                ),

                "city": (
                    database_hotel.city
                    if database_hotel
                    else best.city
                ),

                "area": (
                    database_hotel.area
                    if database_hotel
                    else best.area
                ),

                "rating": (
                    database_hotel.rating
                    if database_hotel
                    else best.rating
                ),

                "stars": (
                    database_hotel.stars
                    if database_hotel
                    else best.stars
                ),

                "description": (
                    database_hotel.description
                    if database_hotel
                    else ""
                ),

                "hotel_id": (
                    database_hotel.id
                    if database_hotel
                    else None
                ),

                "slug": (
                    database_hotel.slug
                    if database_hotel
                    else None
                ),

                "offers": normalized_offers,

                "best": best,

                "provider_count": len(
                    {
                        offer.provider
                        for offer
                        in ranked_offers
                    }
                ),
            }
        )

    results.sort(
        key=lambda item:
        item["best"].effective_price
    )

    return {
        "results": results,

        "provider_errors":
            provider_errors,

        "providers_checked":
            len(providers),

        "raw_offer_count":
            len(all_offers),

        "provider_mode":
            provider_mode,
    }
