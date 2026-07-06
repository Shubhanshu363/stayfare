from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
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


main = Blueprint(
    "main",
    __name__
)


@main.route("/")
def home():

    q = request.args.get(
        "q",
        ""
    ).strip()

    query = Hotel.query

    if q:
        search = f"%{q}%"

        query = query.filter(
            or_(
                Hotel.city.ilike(search),
                Hotel.state.ilike(search),
                Hotel.name.ilike(search),
                Hotel.area.ilike(search),
            )
        )

    hotels = query.all()

    cards = []

    for hotel in hotels:
        cards.append(
            {
                "hotel": hotel,
                "best": best_offer(
                    hotel.offers
                ),
            }
        )

    return render_template(
        "index.html",
        cards=cards,
        q=q,
    )


@main.route("/hotel/<slug>")
def hotel_detail(slug):

    hotel = Hotel.query.filter_by(
        slug=slug
    ).first_or_404()

    offers = rank_offers(
        hotel.offers
    )

    return render_template(
        "hotels/detail.html",
        hotel=hotel,
        offers=offers,
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
        current_user.saved.append(hotel)
        db.session.commit()

        flash(
            "Hotel saved to your shortlist.",
            "success",
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

    alert = PriceAlert(
        user_id=current_user.id,
        hotel_id=hotel_id,
        target_price=target_price,
    )

    db.session.add(alert)
    db.session.commit()

    flash(
        "Price alert created.",
        "success",
    )

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
        return redirect(
            offer.affiliate_url
        )

    flash(
        "Demo mode: a real provider link will be connected here.",
        "info",
    )

    return redirect(
        url_for(
            "main.hotel_detail",
            slug=offer.hotel.slug,
        )
    )
