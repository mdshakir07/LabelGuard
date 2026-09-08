"""fix confidence column types to float

Revision ID: f000bb7c476b
Revises: 3082113b7b58
Create Date: 2026-09-05 12:35:57.912684

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f000bb7c476b'
down_revision: Union[str, Sequence[str], None] = '3082113b7b58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute('ALTER TABLE extracted_fields ALTER COLUMN confidence TYPE FLOAT USING confidence::double precision')
    op.execute('ALTER TABLE findings ALTER COLUMN confidence TYPE FLOAT USING confidence::double precision')


def downgrade() -> None:
    """Downgrade schema."""
    op.execute('ALTER TABLE findings ALTER COLUMN confidence TYPE VARCHAR(20) USING confidence::text')
    op.execute('ALTER TABLE extracted_fields ALTER COLUMN confidence TYPE VARCHAR(20) USING confidence::text')
