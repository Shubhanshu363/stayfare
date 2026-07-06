# Stayfare

Stayfare is a Flask-based hotel deal comparison app for the Indian market. It compares provider offers, ranks them by effective price, and routes users to provider booking flows through tracked affiliate links.

## Quick start

1. Create and activate a virtual environment:
   - python -m venv .venv
   - source .venv/bin/activate
2. Install dependencies:
   - pip install -r requirements.txt
3. Copy the sample environment file and adjust values:
   - cp .env.example .env
4. Initialize the local database:
   - flask db upgrade
5. Run the app:
   - python run.py

## Development notes

- The application defaults to demo provider data unless `PROVIDER_MODE` is set to `LIVE` or `DEGRADED`.
- When Booking.com credentials are configured and `PROVIDER_MODE` is `LIVE` or `DEGRADED`, the app will attempt to include Booking.com inventory in search aggregation.
- The app exposes `/health` and `/provider-status` for basic operational visibility.
- Search, hotel detail, saved hotels, alerts, auth, dashboard, and admin routes remain available.

## Tests

Run the automated regression suite with:
- python -m unittest discover -s tests -p 'test_*.py'

## Migrations

Use Flask-Migrate for schema changes:
- flask db migrate -m "Describe change"
- flask db upgrade
