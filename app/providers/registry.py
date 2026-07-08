from flask import current_app, has_app_context


def build_provider_registry(runtime_mode=None, provider_attempts=None):
    provider_attempts = provider_attempts or []

    providers = {
        "StayBook": {
            "name": "StayBook",
            "configured": True,
            "enabled": True,
            "mode": "DEMO",
            "integration_type": "demo",
            "supported_markets": ["IN"],
            "supported_currency": ["INR"],
            "health": "healthy",
            "latest_successful_request": None,
            "average_response_time_ms": 0,
        },
        "TripNest": {
            "name": "TripNest",
            "configured": True,
            "enabled": True,
            "mode": "DEMO",
            "integration_type": "demo",
            "supported_markets": ["IN"],
            "supported_currency": ["INR"],
            "health": "healthy",
            "latest_successful_request": None,
            "average_response_time_ms": 0,
        },
        "RoomRush": {
            "name": "RoomRush",
            "configured": True,
            "enabled": True,
            "mode": "DEMO",
            "integration_type": "demo",
            "supported_markets": ["IN"],
            "supported_currency": ["INR"],
            "health": "healthy",
            "latest_successful_request": None,
            "average_response_time_ms": 0,
        },
        "Booking.com": {
            "name": "Booking.com",
            "configured": False,
            "enabled": False,
            "mode": "LIVE",
            "integration_type": "live",
            "supported_markets": ["IN"],
            "supported_currency": ["INR"],
            "health": "not-configured",
            "latest_successful_request": None,
            "average_response_time_ms": 0,
        },
    }

    if has_app_context():
        mode = str(runtime_mode or current_app.config.get("PROVIDER_MODE", "DEMO")).upper()
        booking_configured = bool(
            current_app.config.get("BOOKING_API_TOKEN")
            and current_app.config.get("BOOKING_API_BASE_URL")
        )
        providers["Booking.com"]["configured"] = booking_configured
        providers["Booking.com"]["enabled"] = mode in {"LIVE", "DEGRADED"} and booking_configured

        for provider in providers.values():
            provider["mode"] = mode

            if provider["integration_type"] == "demo" and mode in {"LIVE", "DEGRADED"}:
                provider["enabled"] = False

    for attempt in provider_attempts:
        provider_name = attempt.get("provider")
        if provider_name not in providers:
            continue

        providers[provider_name]["average_response_time_ms"] = attempt.get("response_time_ms") or 0
        if attempt.get("succeeded"):
            providers[provider_name]["health"] = "healthy"
            providers[provider_name]["latest_successful_request"] = "recent"
        else:
            providers[provider_name]["health"] = "error"

    return providers
