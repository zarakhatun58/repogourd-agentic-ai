"""merge scraping migration branch

Revision ID: 0f55feb18b7d
Revises: d731f99256a9, f31c9a7b1e22
Create Date: 2026-09-25 01:35:53.119680

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f55feb18b7d'
down_revision: Union[str, Sequence[str], None] = ('d731f99256a9', 'f31c9a7b1e22')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
