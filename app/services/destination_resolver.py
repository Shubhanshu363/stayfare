import re
from .metasearch_domain import CanonicalDestination


ALIASES = {
    "delhi": "New Delhi",
    "new delhi": "New Delhi",
    "goa": "Goa",
    "south goa": "Goa",
    "udaipur": "Udaipur",
    "mumbai": "Mumbai",
    "jaipur": "Jaipur",
    "bengaluru": "Bengaluru",
    "manali": "Manali",
    "rishikesh": "Rishikesh",
}


def _slugify(value):
    value = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower())
    return value.strip("-")


def resolve_destination(query):
    raw_query = (query or "").strip()
    canonical_name = ALIASES.get(raw_query.lower(), raw_query or "Destination")
    if not canonical_name:
        canonical_name = raw_query or "Destination"
    return CanonicalDestination(
        raw_query=raw_query,
        canonical_name=canonical_name,
        provider_key=_slugify(canonical_name),
    )
