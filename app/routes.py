from datetime import date, datetime
from urllib.parse import urlparse

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    current_app,
)

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)

from sqlalchemy import or_

from .extensions import db
from .models import (
    User,
    Hotel,
    Offer,
    PriceAlert,
    AffiliateClick,
)
from .services.deal_engine import (
    rank_offers,
    best_offer,
)


main = Blueprint("main", __name__)


def parse_date(value):
    if not value:
        return None

    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d"
        ).date()
    except ValueError:
        return None


def get_search_context():
    return {
        "destination": request.args.get(
            "destination",
            session.get("destination", "")
        ).strip(),

        "check_in": request.args.get(
            "check_in",
            session.get("check_in", "")
        ),

        "check_out": request.args.get(
            "check_out",
            session.get("check_out", "")
        ),

        "adults": request.args.get(
            "adults",
            session.get("adults", 2),
            type=int
        ) or 2,

        "rooms": request.args.get(
            "rooms",
            session.get("rooms", 1),
            type=int
        ) or 1,
    }


def save_search_context(search):
    for key, value in search.items():
        session[key] = value


def validate_search(search):
    errors = []

    if not search["destination"]:
        errors.append(
            "Please enter a destination, area, or hotel."
        )

    check_in = parse_date(
        search["check_in"]
    )

    check_out = parse_date(
        search["check_out"]
    )

    if search["check_in"] and not check_in:
        errors.append(
            "Please enter a valid check-in date."
        )

    if search["check_out"] and not check_out:
        errors.append(
            "Please enter a valid check-out date."
        )

    if (
        check_in
        and check_out
        and check_out <= check_in
    ):
        errors.append(
            "Check-out must be after check-in."
        )

    if search["adults"] < 1:
        errors.append(
            "At least one guest is required."
        )

    if search["rooms"] < 1:
        errors.append(
            "At least one room is required."
        )

    return errors


@main.route("/")
def home():
    search_query = request.args.get("q", "").strip()

    if search_query:
        search_params = {
            "destination": search_query,
        }

        for key in ("check_in", "check_out"):
            value = request.args.get(key, "").strip()
            if value:
                search_params[key] = value

        adults = request.args.get("adults", type=int)
        rooms = request.args.get("rooms", type=int)

        if adults:
            search_params["adults"] = adults

        if rooms:
            search_params["rooms"] = rooms

        return redirect(
            url_for("main.search", **search_params)
        )

    featured_hotels = Hotel.query.limit(3).all()

    cards = [
        {
            "hotel": hotel,
            "best": best_offer(hotel.offers),
        }
        for hotel in featured_hotels
    ]

    return render_template(
        "index.html",
        cards=cards,
        today=date.today().isoformat(),
        q=search_query,
    )


@main.route("/health")
def health():
    return {
        "status": "ok",
        "app": "stayfare",
        "mode": current_app.config.get("PROVIDER_MODE", "DEMO"),
    }, 200


@main.route("/provider-status")
def provider_status():
    from .services.provider_status import get_provider_status

    return render_template(
        "provider_status.html",
        provider_status=get_provider_status(),
    )


@main.route("/search")
def search():
    from .services.aggregator import (
        aggregate_search,
    )

    search_context = get_search_context()

    errors = validate_search(
        search_context
    )

    if errors:

        for error in errors:
            flash(
                error,
                "error",
            )

        return redirect(
            url_for("main.home")
        )

    save_search_context(
        search_context
    )

    aggregation = aggregate_search(
        destination=search_context[
            "destination"
        ],

        check_in=search_context[
            "check_in"
        ],

        check_out=search_context[
            "check_out"
        ],

        adults=search_context[
            "adults"
        ],

        rooms=search_context[
            "rooms"
        ],
    )

    results = aggregation[
        "results"
    ]

    max_price = request.args.get(
        "max_price",
        type=int,
    )

    min_rating = request.args.get(
        "min_rating",
        type=float,
    )

    stars = request.args.get(
        "stars",
        type=int,
    )

    if max_price:

        results = [
            item
            for item in results
            if (
                item["best"]
                and item[
                    "best"
                ].effective_price
                <= max_price
            )
        ]

    if min_rating:

        results = [
            item
            for item in results
            if (
                item["rating"]
                and item["rating"]
                >= min_rating
            )
        ]

    if stars:

        results = [
            item
            for item in results
            if item["stars"] == stars
        ]

    sort = request.args.get(
        "sort",
        "recommended",
    )

    if sort == "price_low":

        results.sort(
            key=lambda item:
            item[
                "best"
            ].effective_price
        )

    elif sort == "rating":

        results.sort(
            key=lambda item:
            item["rating"] or 0,
            reverse=True,
        )

    elif sort == "savings":

        results.sort(
            key=lambda item:
            item[
                "best"
            ].total_saving,
            reverse=True,
        )

    else:

        results.sort(
            key=lambda item: (
                item["rating"] or 0,
                -item[
                    "best"
                ].effective_price,
            ),
            reverse=True,
        )

    from .services.provider_status import get_provider_status

    return render_template(
        "search/results.html",

        results=results,

        search=search_context,

        sort=sort,

        max_price=max_price,

        min_rating=min_rating,

        stars=stars,

        providers_checked=aggregation[
            "providers_checked"
        ],

        raw_offer_count=aggregation[
            "raw_offer_count"
        ],

        provider_errors=aggregation[
            "provider_errors"
        ],

        provider_status=get_provider_status(),
    )


@main.route("/hotel/<slug>")
def hotel_detail(slug):
    hotel = Hotel.query.filter_by(
        slug=slug
    ).first_or_404()

    search_context = {
        "destination": request.args.get(
            "destination",
            session.get(
                "destination",
                hotel.city
            )
        ),

        "check_in": request.args.get(
            "check_in",
            session.get(
                "check_in",
                ""
            )
        ),

        "check_out": request.args.get(
            "check_out",
            session.get(
                "check_out",
                ""
            )
        ),

        "adults": request.args.get(
            "adults",
            session.get(
                "adults",
                2
            ),
            type=int
        ),

        "rooms": request.args.get(
            "rooms",
            session.get(
                "rooms",
                1
            ),
            type=int
        ),
    }

    offers = rank_offers(
        hotel.offers
    )

    if search_context["destination"]:
        from .services.aggregator import (
            aggregate_search,
        )

        aggregation = aggregate_search(
            destination=search_context[
                "destination"
            ],
            check_in=search_context[
                "check_in"
            ],
            check_out=search_context[
                "check_out"
            ],
            adults=search_context[
                "adults"
            ],
            rooms=search_context[
                "rooms"
            ],
        )

        for result in aggregation["results"]:
            if (
                result.get("slug") == hotel.slug
                or result.get("hotel_id") == hotel.id
                or result.get("name") == hotel.name
            ):
                offers = result.get("offers", offers)
                break

    return render_template(
        "hotels/detail.html",
        hotel=hotel,
        offers=offers,
        search=search_context,
    )


@main.route("/aggregation-test")
def aggregation_test():
    from .services.aggregator import (
        aggregate_search,
    )

    destination = request.args.get(
        "destination",
        "New Delhi",
    ).strip()

    data = aggregate_search(
        destination=destination,
        check_in=request.args.get(
            "check_in"
        ),
        check_out=request.args.get(
            "check_out"
        ),
        adults=request.args.get(
            "adults",
            2,
            type=int,
        ),
        rooms=request.args.get(
            "rooms",
            1,
            type=int,
        ),
    )

    return render_template(
        "search/aggregator_test.html",
        results=data["results"],
        provider_errors=data[
            "provider_errors"
        ],
        providers_checked=data[
            "providers_checked"
        ],
        raw_offer_count=data[
            "raw_offer_count"
        ],
    )


@main.route(
    "/register",
    methods=["GET", "POST"]
)
def register():
    if current_user.is_authenticated:
        return redirect(
            url_for("main.dashboard")
        )

    if request.method == "POST":
        name = request.form[
            "name"
        ].strip()

        email = request.form[
            "email"
        ].lower().strip()

        password = request.form[
            "password"
        ]

        existing = User.query.filter_by(
            email=email
        ).first()

        if existing:
            flash(
                "An account with that email already exists.",
                "error",
            )

            return redirect(
                url_for("main.register")
            )

        if len(password) < 8:
            flash(
                "Password must be at least 8 characters.",
                "error",
            )

            return redirect(
                url_for("main.register")
            )

        user = User(
            name=name,
            email=email,
        )

        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        login_user(user)

        return redirect(
            url_for("main.dashboard")
        )

    return render_template(
        "auth/register.html"
    )


@main.route(
    "/login",
    methods=["GET", "POST"]
)
def login():
    if current_user.is_authenticated:
        return redirect(
            url_for("main.dashboard")
        )

    if request.method == "POST":
        email = request.form[
            "email"
        ].lower().strip()

        password = request.form[
            "password"
        ]

        user = User.query.filter_by(
            email=email
        ).first()

        if (
            user
            and user.check_password(password)
        ):
            login_user(user)

            return redirect(
                url_for("main.dashboard")
            )

        flash(
            "Invalid email or password.",
            "error",
        )

    return render_template(
        "auth/login.html"
    )


@main.route("/logout")
@login_required
def logout():
    logout_user()

    return redirect(
        url_for("main.home")
    )


@main.route(
    "/save/<int:hotel_id>",
    methods=["POST"]
)
@login_required
def save_hotel(hotel_id):
    hotel = db.session.get(
        Hotel,
        hotel_id
    )

    if (
        hotel
        and hotel not in current_user.saved
    ):
        current_user.saved.append(
            hotel
        )

        db.session.commit()

        flash(
            "Hotel saved to your shortlist.",
            "success",
        )

    else:
        flash(
            "This hotel is already in your shortlist.",
            "info",
        )

    return redirect(
        request.referrer
        or url_for("main.dashboard")
    )


@main.route(
    "/alert/<int:hotel_id>",
    methods=["POST"]
)
@login_required
def create_alert(hotel_id):
    hotel = db.session.get(
        Hotel,
        hotel_id
    )

    if not hotel:
        return redirect(
            url_for("main.home")
        )

    target_price = request.form.get(
        "target_price",
        type=int
    )

    existing = PriceAlert.query.filter_by(
        user_id=current_user.id,
        hotel_id=hotel_id,
        active=True,
    ).first()

    if existing:
        existing.target_price = (
            target_price
        )

        flash(
            "Your existing price alert was updated.",
            "success",
        )

    else:
        alert = PriceAlert(
            user_id=current_user.id,
            hotel_id=hotel_id,
            target_price=target_price,
        )

        db.session.add(alert)

        flash(
            "Price alert created.",
            "success",
        )

    db.session.commit()

    return redirect(
        url_for("main.dashboard")
    )


@main.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "dashboard/index.html",
        saved=current_user.saved,
        alerts=current_user.alerts,
    )


@main.route("/admin")
@login_required
def admin():
    if not current_user.is_admin:
        flash(
            "Admin access required.",
            "error",
        )

        return redirect(
            url_for("main.home")
        )

    return render_template(
        "admin/index.html",
        users=User.query.count(),
        hotels=Hotel.query.count(),
        clicks=AffiliateClick.query.count(),
        alerts=PriceAlert.query.count(),
    )


@main.route("/go/<offer_id>")
def affiliate_redirect(offer_id):
    if str(offer_id).isdigit():
        offer = db.session.get(
            Offer,
            int(offer_id)
        )

        if not offer:
            return redirect(
                url_for("main.home")
            )

        click = AffiliateClick(
            hotel_id=offer.hotel_id,
            provider=offer.provider,
        )

        db.session.add(click)
        db.session.commit()

        if (
            offer.affiliate_url
            and offer.affiliate_url != "/"
        ):
            parsed = urlparse(
                offer.affiliate_url
            )

            if parsed.scheme in (
                "http",
                "https",
            ):
                return redirect(
                    offer.affiliate_url
                )

        flash(
            "Demo mode: the real booking partner will open here.",
            "info",
        )

        return redirect(
            url_for(
                "main.hotel_detail",
                slug=offer.hotel.slug,
            )
        )

    parts = str(offer_id).split("|")
    if len(parts) >= 3:
        provider = parts[0]
        hotel_id = int(parts[1]) if parts[1].isdigit() else None
        hotel_slug = parts[2] if parts[2] else None

        if hotel_id is not None:
            click = AffiliateClick(
                hotel_id=hotel_id,
                provider=provider,
            )
            db.session.add(click)
            db.session.commit()

        flash(
            "Demo mode: the real booking partner will open here.",
            "info",
        )

        if hotel_slug:
            return redirect(
                url_for(
                    "main.hotel_detail",
                    slug=hotel_slug,
                )
            )

    return redirect(
        url_for("main.home")
    )
