"""add appointment_id to medical_records

Revision ID: 8954e38c9680
Revises: d2fef7df917b
Create Date: 2026-07-21 13:48:00.935717

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8954e38c9680'
down_revision: Union[str, Sequence[str], None] = 'd2fef7df917b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('medical_records', sa.Column('appointment_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_medical_records_appointment_id', 'medical_records', 'appointments', ['appointment_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_medical_records_appointment_id', 'medical_records', type_='foreignkey')
    op.drop_column('medical_records', 'appointment_id')