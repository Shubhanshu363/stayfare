from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from time import time

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

from .destination_resolver import resolve_destination
from .hotel_matcher import (
    offers_match,
    name_similarity,
    normalize_city,
)
from .metasearch_domain import HotelSearch, ProviderSearchAttempt
from app.providers.registry import build_provider_registry


DEMO_PROVIDERS = [
    MockBookingProvider(),
    MockTravelProvider(),
    MockDealsProvider(),
]

# Backward-compatible alias used by tests that patch provider lists.
PROVIDERS = DEMO_PROVIDERS


def get_providers():
    requested_mode = "DEMO"
    selected_mode = "DEMO"
    providers = list(PROVIDERS)
    live_provider_expected = False

    if has_app_context():
        requested_mode = str(current_app.config.get("PROVIDER_MODE", "DEMO")).upper()

        booking_provider = BookingProvider(
            api_key=current_app.config.get("BOOKING_API_TOKEN"),
            base_url=current_app.config.get("BOOKING_API_BASE_URL"),
            affiliate_id=current_app.config.get("BOOKING_AFFILIATE_ID"),
            timeout=current_app.config.get("BOOKING_API_TIMEOUT_SECONDS"),
        )
        booking_configured = bool(booking_provider.api_key and booking_provider.base_url)

        if requested_mode in {"LIVE", "DEGRADED"} and booking_configured:
            providers = [booking_provider]
            selected_mode = "LIVE"
            live_provider_expected = True
        else:
            providers = list(PROVIDERS)
            selected_mode = "DEMO"

    return {
        "providers": providers,
        "requested_mode": requested_mode,
        "selected_mode": selected_mode,
        "live_provider_expected": live_provider_expected,
    }


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
            mandatory_fees=offer.mandatory_fees,
            discount=offer.discount,
            cashback=offer.cashback,
            verified_coupon_discount=offer.verified_coupon_discount,
            verified_payment_offer=offer.verified_payment_offer,
            room_name=offer.room_name,
            cancellation=offer.cancellation,
            breakfast_included=offer.breakfast_included,
            affiliate_url=offer.affiliate_url,
            rating=offer.rating,
            stars=offer.stars,
            currency=offer.currency,
            room_fingerprint=offer.room_fingerprint,
            comparison_group=offer.comparison_group,
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
    started_at = time()
    try:
        offers = provider.search(
            destination=destination,
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            rooms=rooms,
        )
        return {
            "offers": offers,
            "attempt": ProviderSearchAttempt(
                provider=provider.name,
                started_at=str(started_at),
                completed_at=str(time()),
                succeeded=True,
                response_time_ms=int((time() - started_at) * 1000),
                offers_count=len(offers),
                status="SUCCESS",
            ),
        }
    except Exception as error:
        return {
            "offers": [],
            "attempt": ProviderSearchAttempt(
                provider=provider.name,
                started_at=str(started_at),
                completed_at=str(time()),
                succeeded=False,
                error=str(error),
                response_time_ms=int((time() - started_at) * 1000),
                status="FAILED",
            ),
        }


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
    provider_attempts = []

    search_context = HotelSearch(
        destination=destination,
        check_in=check_in,
        check_out=check_out,
        adults=adults,
        rooms=rooms,
    )
    resolved_destination = resolve_destination(destination)
    provider_plan = get_providers()
    providers = provider_plan["providers"]
    provider_mode = provider_plan["selected_mode"]

    if not providers:
        return {
            "results": [],
            "provider_errors": [{"provider": "system", "error": "No providers available"}],
            "providers_checked": 0,
            "raw_offer_count": 0,
            "provider_mode": "DEMO",
            "search_context": search_context,
            "resolved_destination": resolved_destination,
            "provider_attempts": [],
            "provider_registry": build_provider_registry(
                runtime_mode="DEMO",
                provider_attempts=[],
            ),
        }

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
                outcome = future.result()
                offers = outcome.get("offers", [])
                attempt = outcome.get("attempt")
                provider_attempts.append(
                    {
                        "provider": provider.name,
                        "succeeded": attempt.succeeded,
                        "status": attempt.status,
                        "offers_count": attempt.offers_count,
                        "response_time_ms": attempt.response_time_ms,
                        "error": attempt.error,
                    }
                )

                if not attempt.succeeded:
                    provider_errors.append(
                        {
                            "provider": provider.name,
                            "error": attempt.error or "Provider failed",
                        }
                    )

                all_offers.extend(offers)

            except Exception as error:
                provider_errors.append(
                    {
                        "provider": provider.name,
                        "error": str(error),
                    }
                )

    successful_attempts = [item for item in provider_attempts if item.get("succeeded")]
    if provider_mode == "LIVE":
        if not successful_attempts or provider_errors:
            provider_mode = "DEGRADED"
    elif provider_errors:
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
        "provider_errors": provider_errors,
        "providers_checked": len(providers),
        "raw_offer_count": len(all_offers),
        "provider_mode": provider_mode,
        "search_context": search_context,
        "resolved_destination": resolved_destination,
        "provider_attempts": provider_attempts,
        "provider_registry": build_provider_registry(
            runtime_mode=provider_mode,
            provider_attempts=provider_attempts,
        ),
    }
