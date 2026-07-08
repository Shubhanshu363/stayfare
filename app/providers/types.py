from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProviderOffer:
    provider: str
    provider_hotel_id: str
    hotel_name: str
    city: str
    area: str

    listed_price: int
    taxes: int = 0
    mandatory_fees: int = 0
    discount: int = 0
    cashback: int = 0
    verified_coupon_discount: int = 0
    verified_payment_offer: int = 0

    room_name: str = "Standard Room"
    cancellation: str = "Cancellation policy varies"
    breakfast_included: bool = False
    affiliate_url: str = "/"

    rating: Optional[float] = None
    stars: Optional[int] = None
    currency: str = "INR"
    room_fingerprint: Optional[dict] = None
    comparison_group: str = "EXACT OR HIGHLY COMPARABLE"

    metadata: dict = field(
        default_factory=dict
    )

    @property
    def base_price(self):
        return self.listed_price

    @property
    def total_stay_price(self):
        return max(
            0,
            self.listed_price
            + self.taxes
            + self.mandatory_fees
        )

    @property
    def payable_now(self):
        return max(
            0,
            self.total_stay_price
            - self.discount
            - self.verified_coupon_discount
            - self.verified_payment_offer
        )

    @property
    def effective_price(self):
        return max(
            0,
            self.payable_now
            - self.cashback
        )

    @property
    def total_saving(self):
        return (
            self.discount
            + self.verified_coupon_discount
            + self.verified_payment_offer
            + self.cashback
        )
