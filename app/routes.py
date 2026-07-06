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
    )


@main.route("/search")
def search():
    search_context = get_search_context()

    errors = validate_search(
        search_context
    )

    if errors:
        for error in errors:
            flash(error, "error")

        return redirect(
            url_for("main.home")
        )

    save_search_context(
        search_context
    )

    destination = (
        search_context["destination"]
    )

    search_term = f"%{destination}%"

    hotels = Hotel.query.filter(
        or_(
            Hotel.city.ilike(search_term),
            Hotel.state.ilike(search_term),
            Hotel.name.ilike(search_term),
            Hotel.area.ilike(search_term),
        )
    ).all()

    results = []

    for hotel in hotels:
        ranked = rank_offers(
            hotel.offers
        )

        best = (
            ranked[0]
            if ranked
            else None
        )

        results.append(
            {
                "hotel": hotel,
                "best": best,
                "offers_count": len(ranked),
            }
        )

    max_price = request.args.get(
        "max_price",
        type=int
    )

    min_rating = request.args.get(
        "min_rating",
        type=float
    )

    stars = request.args.get(
        "stars",
        type=int
    )

    if max_price:
        results = [
            item
            for item in results
            if item["best"]
            and item["best"].effective_price
            <= max_price
        ]

    if min_rating:
        results = [
            item
            for item in results
            if item["hotel"].rating
            >= min_rating
        ]

    if stars:
        results = [
            item
            for item in results
            if item["hotel"].stars
            == stars
        ]

    sort = request.args.get(
        "sort",
        "recommended"
    )

    if sort == "price_low":
        results.sort(
            key=lambda item:
            item["best"].effective_price
            if item["best"]
            else float("inf")
        )

    elif sort == "rating":
        results.sort(
            key=lambda item:
            item["hotel"].rating,
            reverse=True
        )

    elif sort == "savings":
        results.sort(
            key=lambda item:
            item["best"].total_saving
            if item["best"]
            else 0,
            reverse=True
        )

    else:
        results.sort(
            key=lambda item: (
                item["hotel"].rating,
                -item["best"].effective_price
                if item["best"]
                else 0,
            ),
            reverse=True
        )

    return render_template(
        "search/results.html",
        results=results,
        search=search_context,
        sort=sort,
        max_price=max_price,
        min_rating=min_rating,
        stars=stars,
    )


@main.route("/hotel/<slug>")
def hotel_detail(slug):
    hotel = Hotel.query.filter_by(
        slug=slug
    ).first_or_404()

    offers = rank_offers(
        hotel.offers
    )

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

    return render_template(
        "hotels/detail.html",
        hotel=hotel,
        offers=offers,
        search=search_context,
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


@main.route("/go/<int:offer_id>")
def affiliate_redirect(offer_id):
    offer = db.session.get(
        Offer,
        offer_id
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
