import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .base import HotelProvider
from .types import ProviderOffer


class BookingProvider(HotelProvider):

    name = "Booking.com"

    def __init__(
        self,
        api_key=None,
        base_url=None,
        affiliate_id=None,
        timeout=None,
    ):
        self.api_key = api_key or os.getenv("BOOKING_API_TOKEN")
        self.base_url = base_url or os.getenv("BOOKING_API_BASE_URL")
        self.affiliate_id = affiliate_id or os.getenv("BOOKING_AFFILIATE_ID")
        self.timeout = int(
            timeout
            or os.getenv(
                "BOOKING_API_TIMEOUT_SECONDS",
                os.getenv("PROVIDER_TIMEOUT_SECONDS", "5"),
            )
        )

    def search(
        self,
        destination,
        check_in=None,
        check_out=None,
        adults=2,
        rooms=1,
    ):
        if not self.api_key or not self.base_url:
            return []

        params = {
            "q": destination,
            "adults": adults,
            "rooms": rooms,
        }

        if check_in:
            params["check_in"] = check_in

        if check_out:
            params["check_out"] = check_out

        if self.affiliate_id:
            params["affiliate_id"] = self.affiliate_id

        url = f"{self.base_url.rstrip('/')}/search?{urlencode(params)}"
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )

        if self.affiliate_id:
            request.add_header("X-Partner-Id", self.affiliate_id)

        with urlopen(request, timeout=self.timeout) as response:
            payload = response.read()

        if isinstance(payload, (bytes, bytearray)):
            payload = payload.decode("utf-8")

        if isinstance(payload, str):
            payload = json.loads(payload)

        if isinstance(payload, dict):
            raw_results = payload.get("results", [])
        else:
            raw_results = payload

        offers = []

        for item in raw_results:
            if not isinstance(item, dict):
                continue

            listed_price = int(item.get("price", 0) or 0)
            taxes = int(item.get("taxes", 0) or 0)
            discount = int(item.get("discount", 0) or 0)
            cashback = int(item.get("cashback", 0) or 0)

            offers.append(
                ProviderOffer(
                    provider=self.name,
                    provider_hotel_id=str(item.get("hotel_id") or item.get("id") or ""),
                    hotel_name=item.get("name", destination),
                    city=item.get("city", destination),
                    area=item.get("area", ""),
                    listed_price=listed_price,
                    taxes=taxes,
                    discount=discount,
                    cashback=cashback,
                    room_name=item.get("room_name", "Standard Room"),
                    cancellation=item.get("cancellation", "Cancellation policy varies"),
                    breakfast_included=bool(item.get("breakfast_included", False)),
                    rating=item.get("rating"),
                    stars=item.get("stars"),
                    metadata={
                        "source": "booking.com",
                        "raw": item,
                    },
                )
            )

        return offers
