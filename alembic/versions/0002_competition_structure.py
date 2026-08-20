from alembic import op
import sqlalchemy as sa

revision = '0002_competition_structure'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    existing = set(inspector.get_table_names())
    if 'historical_competition_rules' not in existing:
        op.create_table(
        'historical_competition_rules',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('scope', sa.String(length=40), nullable=False),
        sa.Column('country_id', sa.Integer(), sa.ForeignKey('countries.id'), nullable=True),
        sa.Column('name', sa.String(length=140), nullable=False),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('valid_to', sa.Date(), nullable=True),
        sa.Column('format', sa.String(length=40), nullable=False),
        sa.Column('min_clubs', sa.Integer(), nullable=False),
        sa.Column('max_clubs', sa.Integer(), nullable=False),
        sa.Column('matches_per_opponent', sa.Integer(), nullable=False),
        sa.Column('season_start_month', sa.Integer(), nullable=False),
        sa.Column('season_end_month', sa.Integer(), nullable=False),
        sa.Column('international', sa.Boolean(), nullable=False),
    )
    if 'standings' not in existing:
        op.create_table(
        'standings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('season_id', sa.Integer(), sa.ForeignKey('seasons.id'), nullable=False),
        sa.Column('club_id', sa.Integer(), sa.ForeignKey('clubs.id'), nullable=False),
        sa.Column('played', sa.Integer(), nullable=False),
        sa.Column('wins', sa.Integer(), nullable=False),
        sa.Column('draws', sa.Integer(), nullable=False),
        sa.Column('losses', sa.Integer(), nullable=False),
        sa.Column('goals_for', sa.Integer(), nullable=False),
        sa.Column('goals_against', sa.Integer(), nullable=False),
        sa.Column('goal_difference', sa.Integer(), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
    )
    if 'standings' not in existing:
        op.create_index('ix_standings_season_id', 'standings', ['season_id'])
    if 'standings' not in existing:
        op.create_index('ix_standings_club_id', 'standings', ['club_id'])
    if 'club_coefficients' not in existing:
        op.create_table(
        'club_coefficients',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('world_id', sa.String(length=36), sa.ForeignKey('game_worlds.id'), nullable=False),
        sa.Column('club_id', sa.Integer(), sa.ForeignKey('clubs.id'), nullable=False),
        sa.Column('season_year', sa.Integer(), nullable=False),
        sa.Column('participation_points', sa.Float(), nullable=False),
        sa.Column('result_points', sa.Float(), nullable=False),
        sa.Column('progression_points', sa.Float(), nullable=False),
        sa.Column('coefficient', sa.Float(), nullable=False),
    )
    if 'club_coefficients' not in existing:
        op.create_index('ix_club_coefficients_world_id', 'club_coefficients', ['world_id'])
    if 'club_coefficients' not in existing:
        op.create_index('ix_club_coefficients_club_id', 'club_coefficients', ['club_id'])
    if 'club_coefficients' not in existing:
        op.create_index('ix_club_coefficients_season_year', 'club_coefficients', ['season_year'])
    if 'country_coefficients' not in existing:
        op.create_table(
        'country_coefficients',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('world_id', sa.String(length=36), sa.ForeignKey('game_worlds.id'), nullable=False),
        sa.Column('country_id', sa.Integer(), sa.ForeignKey('countries.id'), nullable=False),
        sa.Column('season_year', sa.Integer(), nullable=False),
        sa.Column('coefficient', sa.Float(), nullable=False),
        sa.Column('club_count', sa.Integer(), nullable=False),
    )
    if 'country_coefficients' not in existing:
        op.create_index('ix_country_coefficients_world_id', 'country_coefficients', ['world_id'])
    if 'country_coefficients' not in existing:
        op.create_index('ix_country_coefficients_country_id', 'country_coefficients', ['country_id'])
    if 'country_coefficients' not in existing:
        op.create_index('ix_country_coefficients_season_year', 'country_coefficients', ['season_year'])


def downgrade():
    op.drop_index('ix_country_coefficients_season_year', table_name='country_coefficients')
    op.drop_index('ix_country_coefficients_country_id', table_name='country_coefficients')
    op.drop_index('ix_country_coefficients_world_id', table_name='country_coefficients')
    op.drop_table('country_coefficients')
    op.drop_index('ix_club_coefficients_season_year', table_name='club_coefficients')
    op.drop_index('ix_club_coefficients_club_id', table_name='club_coefficients')
    op.drop_index('ix_club_coefficients_world_id', table_name='club_coefficients')
    op.drop_table('club_coefficients')
    op.drop_index('ix_standings_club_id', table_name='standings')
    op.drop_index('ix_standings_season_id', table_name='standings')
    op.drop_table('standings')
    op.drop_table('historical_competition_rules')
