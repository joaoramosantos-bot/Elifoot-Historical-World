from alembic import op
import sqlalchemy as sa

revision = '0003_player_club_and_match_dates'
down_revision = '0002_competition_structure'
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {col['name'] for col in inspector.get_columns('game_worlds')}
    if 'player_club_id' not in columns:
        op.add_column('game_worlds', sa.Column('player_club_id', sa.Integer(), nullable=True))
        # SQLite cannot add a foreign-key constraint after table creation; other DBs can still
        # rely on ORM metadata when creating a fresh schema.


def downgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {col['name'] for col in inspector.get_columns('game_worlds')}
    if 'player_club_id' in columns:
        op.drop_column('game_worlds', 'player_club_id')
