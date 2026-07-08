from dataclasses import dataclass
from typing import Optional


@dataclass
class CanonicalDestination:
    raw_query: str
    canonical_name: str
    provider_key: str
    country: str = "IN"
    market: str = "IN"


@dataclass
class HotelSearch:
    destination: str
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    adults: int = 2
    rooms: int = 1
    currency: str = "INR"


@dataclass
class ProviderSearchAttempt:
    provider: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    succeeded: bool = False
    error: Optional[str] = None
    response_time_ms: Optional[int] = None
    offers_count: int = 0
    status: str = "PENDING"


@dataclass
class Saving:
    source: str
    kind: str
    amount: int = 0
    eligibility: str = "everyone"
    confidence: str = "verified"
    expiry: Optional[str] = None
    terms_summary: str = ""


@dataclass
class PriceBreakdown:
    base_price: int = 0
    taxes: int = 0
    mandatory_fees: int = 0
    provider_discount: int = 0
    verified_coupon_discount: int = 0
    verified_payment_offer: int = 0
    verified_cashback: int = 0


@dataclass
class RoomFingerprint:
    room_name: str = ""
    room_category: str = ""
    bed_type: str = ""
    occupancy: str = ""
    room_size: Optional[str] = None
    view: Optional[str] = None
    meal_plan: Optional[str] = None
    cancellation_flexibility: Optional[str] = None
