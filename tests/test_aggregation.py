import json
import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DATABASE_URL", "sqlite:///" + tempfile.NamedTemporaryFile(suffix=".db", delete=False).name)

from app import create_app, db
from app.providers.booking import BookingProvider
from app.services.aggregator import aggregate_search


class AggregationFlowTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        cls.client = cls.app.test_client()

        with cls.app.app_context():
            db.create_all()

    def setUp(self):
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_new_delhi_search_groups_three_provider_offers_into_one_hotel(self):
        with self.app.app_context():
            data = aggregate_search(destination="New Delhi")

        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["raw_offer_count"], 3)
        self.assertEqual(data["results"][0]["provider_count"], 3)
        self.assertEqual(data["results"][0]["name"], "The Leela Palace New Delhi")

    def test_tripnest_is_ranked_first_for_new_delhi(self):
        with self.app.app_context():
            data = aggregate_search(destination="New Delhi")

        result = data["results"][0]
        self.assertEqual(result["best"].provider, "TripNest")
        self.assertEqual(result["best"].effective_price, 16400)

    def test_search_results_link_to_internal_hotel_detail_page(self):
        response = self.client.get("/search?destination=New+Delhi")

        self.assertEqual(response.status_code, 200)
        self.assertIn("/hotel/leela-palace-new-delhi", response.get_data(as_text=True))

    def test_hotel_detail_page_shows_all_aggregated_provider_offers(self):
        response = self.client.get(
            "/hotel/leela-palace-new-delhi?destination=New+Delhi"
        )

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("TripNest", html)
        self.assertIn("StayBook", html)
        self.assertIn("RoomRush", html)
        self.assertIn("Effective price", html)

    def test_provider_failure_does_not_crash_search(self):
        class FailingProvider:
            name = "Broken Provider"

            def search(self, *args, **kwargs):
                raise RuntimeError("provider down")

        with patch("app.services.aggregator.PROVIDERS", [FailingProvider()]):
            with self.app.app_context():
                data = aggregate_search(destination="New Delhi")

        self.assertEqual(data["raw_offer_count"], 0)
        self.assertEqual(data["results"], [])
        self.assertEqual(len(data["provider_errors"]), 1)
        self.assertEqual(data["provider_mode"], "DEGRADED")

    def test_booking_provider_uses_configured_credentials_and_normalizes_pricing(self):
        payload = {
            "results": [
                {
                    "hotel_id": "bk-100",
                    "name": "The Leela Palace New Delhi",
                    "city": "New Delhi",
                    "area": "Chanakyapuri",
                    "price": 14500,
                    "taxes": 1100,
                    "discount": 2200,
                    "cashback": 500,
                    "room_name": "Deluxe Room",
                    "cancellation": "Free cancellation",
                    "breakfast_included": True,
                    "rating": 4.8,
                    "stars": 5,
                }
            ]
        }

        class MockResponse:
            def __init__(self, payload):
                self._payload = payload

            def read(self):
                return json.dumps(self._payload).encode("utf-8")

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        with patch("app.providers.booking.urlopen", return_value=MockResponse(payload)):
            provider = BookingProvider(
                api_key="secret",
                base_url="https://example.test",
                affiliate_id="partner",
                timeout=2,
            )
            offers = provider.search("New Delhi")

        self.assertEqual(len(offers), 1)
        self.assertEqual(offers[0].provider, "Booking.com")
        self.assertEqual(offers[0].provider_hotel_id, "bk-100")
        self.assertEqual(offers[0].listed_price, 14500)
        self.assertEqual(offers[0].effective_price, 12900)

    def test_homepage_search_redirects_to_search_results(self):
        response = self.client.get("/?q=New+Delhi")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/search?destination=New+Delhi", response.headers.get("Location", ""))

    def test_authentication_and_dashboard_routes_still_load(self):
        login_response = self.client.get("/login")
        self.assertEqual(login_response.status_code, 200)

        dashboard_response = self.client.get("/dashboard")
        self.assertEqual(dashboard_response.status_code, 302)
        self.assertIn("login", dashboard_response.headers.get("Location", ""))


if __name__ == "__main__":
    unittest.main()
