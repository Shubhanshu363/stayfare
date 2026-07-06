from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)

from .extensions import db, login_manager


saved_hotels = db.Table(
    "saved_hotels",
    db.Column(
        "user_id",
        db.Integer,
        db.ForeignKey("user.id"),
        primary_key=True,
    ),
    db.Column(
        "hotel_id",
        db.Integer,
        db.ForeignKey("hotel.id"),
        primary_key=True,
    ),
)


class User(UserMixin, db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(120),
        nullable=False
    )

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    is_admin = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    saved = db.relationship(
        "Hotel",
        secondary=saved_hotels,
        backref="saved_by"
    )

    alerts = db.relationship(
        "PriceAlert",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(
            self.password_hash,
            password
        )


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(
        User,
        int(user_id)
    )


class Hotel(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    slug = db.Column(
        db.String(180),
        unique=True,
        nullable=False
    )

    name = db.Column(
        db.String(255),
        nullable=False
    )

    city = db.Column(
        db.String(120),
        nullable=False,
        index=True
    )

    state = db.Column(
        db.String(120),
        nullable=False
    )

    area = db.Column(
        db.String(180)
    )

    stars = db.Column(
        db.Integer,
        default=5
    )

    rating = db.Column(
        db.Float,
        default=4.5
    )

    reviews = db.Column(
        db.Integer,
        default=0
    )

    description = db.Column(
        db.Text
    )

    offers = db.relationship(
        "Offer",
        backref="hotel",
        lazy=True,
        cascade="all, delete-orphan"
    )

    restaurants = db.relationship(
        "Restaurant",
        backref="hotel",
        lazy=True,
        cascade="all, delete-orphan"
    )


class Offer(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    hotel_id = db.Column(
        db.Integer,
        db.ForeignKey("hotel.id"),
        nullable=False
    )

    provider = db.Column(
        db.String(120),
        nullable=False
    )

    room_name = db.Column(
        db.String(180),
        default="Deluxe Room"
    )

    listed_price = db.Column(
        db.Integer,
        nullable=False
    )

    taxes = db.Column(
        db.Integer,
        default=0
    )

    discount = db.Column(
        db.Integer,
        default=0
    )

    cashback = db.Column(
        db.Integer,
        default=0
    )

    cancellation = db.Column(
        db.String(180),
        default="Free cancellation"
    )

    breakfast_included = db.Column(
        db.Boolean,
        default=False
    )

    affiliate_url = db.Column(
        db.String(1000),
        default="/"
    )

    @property
    def payable_now(self):
        return max(
            0,
            self.listed_price
            + self.taxes
            - self.discount
        )

    @property
    def effective_price(self):
        return max(
            0,
            self.payable_now
            - self.cashback
        )

    @property
    def total_saving(self):
        return (
            self.discount
            + self.cashback
        )


class Restaurant(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    hotel_id = db.Column(
        db.Integer,
        db.ForeignKey("hotel.id"),
        nullable=False
    )

    name = db.Column(
        db.String(255),
        nullable=False
    )

    cuisine = db.Column(
        db.String(255)
    )

    occasion = db.Column(
        db.String(120)
    )

    travel_minutes = db.Column(
        db.Integer
    )

    rating = db.Column(
        db.Float
    )

    price_level = db.Column(
        db.String(20)
    )


class PriceAlert(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    hotel_id = db.Column(
        db.Integer,
        db.ForeignKey("hotel.id"),
        nullable=False
    )

    target_price = db.Column(
        db.Integer
    )

    active = db.Column(
        db.Boolean,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    hotel = db.relationship("Hotel")


class AffiliateClick(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    hotel_id = db.Column(
        db.Integer
    )

    provider = db.Column(
        db.String(120)
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
