"""metasearch domain support

Revision ID: 20260708
Revises: 
Create Date: 2026-07-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by alembic.
revision = '20260708'
down_revision = None
branch_labels = None
depends_on = None


def _has_column(table_name, column_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [column["name"] for column in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    if not _has_column('offer', 'mandatory_fees'):
        op.add_column('offer', sa.Column('mandatory_fees', sa.Integer(), nullable=True, server_default='0'))
    if not _has_column('offer', 'verified_coupon_discount'):
        op.add_column('offer', sa.Column('verified_coupon_discount', sa.Integer(), nullable=True, server_default='0'))
    if not _has_column('offer', 'verified_payment_offer'):
        op.add_column('offer', sa.Column('verified_payment_offer', sa.Integer(), nullable=True, server_default='0'))
    if not _has_column('offer', 'provider_hotel_id'):
        op.add_column('offer', sa.Column('provider_hotel_id', sa.String(length=255), nullable=True))
    if not _has_column('offer', 'currency'):
        op.add_column('offer', sa.Column('currency', sa.String(length=20), nullable=True, server_default='INR'))
    if not _has_column('offer', 'room_fingerprint'):
        op.add_column('offer', sa.Column('room_fingerprint', sa.Text(), nullable=True))
    if not _has_column('offer', 'comparison_group'):
        op.add_column('offer', sa.Column('comparison_group', sa.String(length=80), nullable=True, server_default='EXACT OR HIGHLY COMPARABLE'))
    if not _has_column('hotel', 'canonical_slug'):
        op.add_column('hotel', sa.Column('canonical_slug', sa.String(length=180), nullable=True))


def downgrade():
    if _has_column('offer', 'comparison_group'):
        op.drop_column('offer', 'comparison_group')
    if _has_column('offer', 'room_fingerprint'):
        op.drop_column('offer', 'room_fingerprint')
    if _has_column('offer', 'currency'):
        op.drop_column('offer', 'currency')
    if _has_column('offer', 'provider_hotel_id'):
        op.drop_column('offer', 'provider_hotel_id')
    if _has_column('offer', 'verified_payment_offer'):
        op.drop_column('offer', 'verified_payment_offer')
    if _has_column('offer', 'verified_coupon_discount'):
        op.drop_column('offer', 'verified_coupon_discount')
    if _has_column('offer', 'mandatory_fees'):
        op.drop_column('offer', 'mandatory_fees')
    if _has_column('hotel', 'canonical_slug'):
        op.drop_column('hotel', 'canonical_slug')
