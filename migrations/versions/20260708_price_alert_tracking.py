"""price alert tracking and price observations

Revision ID: 20260708b
Revises: 20260708
Create Date: 2026-07-08 00:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260708b"
down_revision = "20260708"
branch_labels = None
depends_on = None


def _has_column(table_name, column_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [column["name"] for column in inspector.get_columns(table_name)]
    return column_name in columns


def _has_table(table_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade():
    if not _has_column("price_alert", "check_in"):
        op.add_column("price_alert", sa.Column("check_in", sa.Date(), nullable=True))
    if not _has_column("price_alert", "check_out"):
        op.add_column("price_alert", sa.Column("check_out", sa.Date(), nullable=True))
    if not _has_column("price_alert", "adults"):
        op.add_column("price_alert", sa.Column("adults", sa.Integer(), nullable=True, server_default="2"))
    if not _has_column("price_alert", "rooms"):
        op.add_column("price_alert", sa.Column("rooms", sa.Integer(), nullable=True, server_default="1"))
    if not _has_column("price_alert", "baseline_price"):
        op.add_column("price_alert", sa.Column("baseline_price", sa.Integer(), nullable=True))
    if not _has_column("price_alert", "latest_price"):
        op.add_column("price_alert", sa.Column("latest_price", sa.Integer(), nullable=True))
    if not _has_column("price_alert", "lowest_observed_price"):
        op.add_column("price_alert", sa.Column("lowest_observed_price", sa.Integer(), nullable=True))
    if not _has_column("price_alert", "currency"):
        op.add_column("price_alert", sa.Column("currency", sa.String(length=20), nullable=True, server_default="INR"))
    if not _has_column("price_alert", "last_checked"):
        op.add_column("price_alert", sa.Column("last_checked", sa.DateTime(), nullable=True))

    if not _has_table("price_observation"):
        op.create_table(
            "price_observation",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("hotel_id", sa.Integer(), nullable=False),
            sa.Column("provider", sa.String(length=120), nullable=True),
            sa.Column("room_fingerprint", sa.String(length=255), nullable=True),
            sa.Column("payable_price", sa.Integer(), nullable=True),
            sa.Column("effective_price", sa.Integer(), nullable=True),
            sa.Column("currency", sa.String(length=20), nullable=True, server_default="INR"),
            sa.Column("check_in", sa.Date(), nullable=True),
            sa.Column("check_out", sa.Date(), nullable=True),
            sa.Column("adults", sa.Integer(), nullable=True, server_default="2"),
            sa.Column("rooms", sa.Integer(), nullable=True, server_default="1"),
            sa.Column("observed_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["hotel_id"], ["hotel.id"]),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade():
    if _has_table("price_observation"):
        op.drop_table("price_observation")

    if _has_column("price_alert", "last_checked"):
        op.drop_column("price_alert", "last_checked")
    if _has_column("price_alert", "currency"):
        op.drop_column("price_alert", "currency")
    if _has_column("price_alert", "lowest_observed_price"):
        op.drop_column("price_alert", "lowest_observed_price")
    if _has_column("price_alert", "latest_price"):
        op.drop_column("price_alert", "latest_price")
    if _has_column("price_alert", "baseline_price"):
        op.drop_column("price_alert", "baseline_price")
    if _has_column("price_alert", "rooms"):
        op.drop_column("price_alert", "rooms")
    if _has_column("price_alert", "adults"):
        op.drop_column("price_alert", "adults")
    if _has_column("price_alert", "check_out"):
        op.drop_column("price_alert", "check_out")
    if _has_column("price_alert", "check_in"):
        op.drop_column("price_alert", "check_in")
