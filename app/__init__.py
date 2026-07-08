from datetime import datetime

import click
from flask import Flask

from config import Config, DevelopmentConfig, TestingConfig, ProductionConfig
from .extensions import db, login_manager, migrate


def create_app(config_object=None):
    app = Flask(__name__)

    if config_object is None:
        env = app.config.get("ENV", "development")
        if env == "testing":
            config_object = TestingConfig
        elif env == "production":
            config_object = ProductionConfig
        else:
            config_object = DevelopmentConfig

    app.config.from_object(config_object)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    from .routes import main
    app.register_blueprint(main)

    @app.cli.command("alerts-check")
    def alerts_check_command():
        """Recheck active price alerts and store price observations."""
        from .models import PriceAlert, PriceObservation
        from .services.aggregator import aggregate_search

        active_alerts = PriceAlert.query.filter_by(active=True).all()
        updated = 0
        triggered = 0

        for alert in active_alerts:
            if not alert.hotel:
                continue

            search_data = aggregate_search(
                destination=alert.hotel.city,
                check_in=alert.check_in.isoformat() if alert.check_in else None,
                check_out=alert.check_out.isoformat() if alert.check_out else None,
                adults=alert.adults or 2,
                rooms=alert.rooms or 1,
            )

            best_result = None
            for result in search_data.get("results", []):
                if result.get("hotel_id") == alert.hotel_id:
                    best_result = result
                    break
                if result.get("slug") and result.get("slug") == alert.hotel.slug:
                    best_result = result
                    break

            if not best_result or not best_result.get("best"):
                continue

            best_offer = best_result["best"]
            latest_price = best_offer.effective_price

            alert.latest_price = latest_price
            alert.last_checked = datetime.utcnow()
            if alert.baseline_price is None:
                alert.baseline_price = latest_price
            if alert.lowest_observed_price is None:
                alert.lowest_observed_price = latest_price
            else:
                alert.lowest_observed_price = min(alert.lowest_observed_price, latest_price)

            db.session.add(
                PriceObservation(
                    hotel_id=alert.hotel_id,
                    provider=best_offer.provider,
                    room_fingerprint=best_offer.room_name,
                    payable_price=best_offer.payable_now,
                    effective_price=best_offer.effective_price,
                    currency=best_offer.currency,
                    check_in=alert.check_in,
                    check_out=alert.check_out,
                    adults=alert.adults or 2,
                    rooms=alert.rooms or 1,
                )
            )

            if alert.target_price and latest_price <= alert.target_price:
                triggered += 1

            updated += 1

        db.session.commit()
        click.echo(
            f"Checked {len(active_alerts)} active alerts; updated {updated}; triggered {triggered}."
        )

    with app.app_context():
        db.create_all()

        from .seed import seed_demo_data
        try:
            seed_demo_data()
        except Exception:
            app.logger.exception("Demo seed skipped due to schema mismatch during startup")

    return app
