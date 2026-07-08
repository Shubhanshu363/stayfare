import unittest

from app.providers.types import ProviderOffer
from app.providers.registry import build_provider_registry
from app.services.destination_resolver import resolve_destination


class MetasearchDomainTests(unittest.TestCase):
    def test_offer_normalization_calculates_total_stay_and_effective_price(self):
        offer = ProviderOffer(
            provider="StayBook",
            provider_hotel_id="sb-1",
            hotel_name="The Leela Palace",
            city="New Delhi",
            area="Chanakyapuri",
            listed_price=15000,
            taxes=1200,
            mandatory_fees=500,
            discount=2000,
            cashback=400,
            room_name="Deluxe Room",
            cancellation="Free cancellation",
            breakfast_included=True,
        )

        self.assertEqual(offer.total_stay_price, 16700)
        self.assertEqual(offer.payable_now, 14700)
        self.assertEqual(offer.effective_price, 14300)
        self.assertEqual(offer.comparison_group, "EXACT OR HIGHLY COMPARABLE")

    def test_destination_resolver_normalizes_indian_aliases(self):
        resolved = resolve_destination("Delhi")
        self.assertEqual(resolved.canonical_name, "New Delhi")
        self.assertEqual(resolved.provider_key, "new-delhi")

    def test_provider_registry_exposes_enabled_status_and_mode(self):
        registry = build_provider_registry()
        self.assertIn("StayBook", registry)
        self.assertTrue(registry["StayBook"]["enabled"])
        self.assertEqual(registry["StayBook"]["mode"], "DEMO")


if __name__ == "__main__":
    unittest.main()
