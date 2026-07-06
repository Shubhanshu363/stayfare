from flask import current_app


def get_provider_status():
    mode = str(current_app.config.get("PROVIDER_MODE", "DEMO")).upper()

    if mode == "LIVE":
        label = "Live inventory"
        detail = "Using live provider inventory when available."
    elif mode == "DEGRADED":
        label = "Degraded mode"
        detail = "Some providers are unavailable; showing verified fallback results."
    else:
        label = "Demo inventory"
        detail = "Showing demo provider data for local development and previews."

    return {
        "mode": mode,
        "label": label,
        "detail": detail,
    }
