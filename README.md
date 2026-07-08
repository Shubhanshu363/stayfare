# Stayfare

Stayfare is a Flask-based hotel deal comparison app for the Indian market. It compares provider offers, ranks them by effective price, and routes users to provider booking flows through tracked affiliate links.

Core promise: Search once. Compare hotel prices. Book with the provider.

## Quick start

1. Create and activate a virtual environment:
   - python -m venv .venv
   - source .venv/bin/activate
2. Install dependencies:
   - pip install -r requirements.txt
3. Copy the sample environment file and adjust values:
   - cp .env.example .env
4. Initialize the local database:
   - export FLASK_APP=run.py
   - python -m flask db upgrade
5. Run the app:
   - python run.py

## Development notes

- The application defaults to demo provider data.
- `PROVIDER_MODE=DEMO`: only demo providers are queried.
- `PROVIDER_MODE=LIVE` with valid Booking credentials: only live provider data is queried.
- `PROVIDER_MODE=LIVE` without valid Booking credentials: the app falls back to demo mode.
- `PROVIDER_MODE=DEGRADED` is used at runtime when a live provider is expected but fails or times out.
- The app exposes `/health` and `/provider-status` for basic operational visibility.
- Search, hotel detail, saved hotels, alerts, auth, dashboard, and admin routes remain available.
- Price alert rechecks run through CLI and are scheduler-friendly (`alerts-check`).

## Provider credentials

Booking.com integration is implemented and credential-ready.

- `BOOKING_API_TOKEN`
- `BOOKING_API_BASE_URL`
- `BOOKING_AFFILIATE_ID` (optional but recommended)
- `BOOKING_API_TIMEOUT_SECONDS`

If these values are missing, Stayfare runs in demo mode and does not claim live provider pricing.

## Tests

Run the automated regression suite with:
- python -m unittest discover -s tests -p 'test_*.py'

Run syntax checks:
- python -m compileall app

Run a quick provider smoke check:
- python -m unittest tests.test_aggregation.AggregationFlowTestCase.test_booking_provider_uses_configured_credentials_and_normalizes_pricing

## Migrations

Use Flask-Migrate for schema changes:
- flask db migrate -m "Describe change"
- flask db upgrade

## Price alerts recheck

Run alert rechecks outside requests:
- export FLASK_APP=run.py
- python -m flask alerts-check

This command updates alert latest/lowest values and records price observations.
