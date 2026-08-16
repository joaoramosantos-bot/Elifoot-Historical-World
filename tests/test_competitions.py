from datetime import date
from uuid import uuid4

from sqlalchemy import create_engine, select
import tempfile
from sqlalchemy.orm import sessionmaker
from app.db import Base
from app.engine import SimulationEngine
from app.models import (
    Club, ClubCoefficient, Competition, Country, CountryCoefficient, GameWorld,
    HistoricalCompetitionRule, Match, Season, Standing,
)


def session():
    db_file = tempfile.NamedTemporaryFile(suffix=".db")
    engine = create_engine(f"sqlite:///{db_file.name}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    db._tmp_file = db_file
    return db


def world(db, current_date=date(1900, 9, 1)):
    w = GameWorld(id=str(uuid4()), name="W", current_date=current_date, seed=1, created_at=current_date)
    db.add(w); db.flush(); return w


def country(db, w):
    c = Country(world_id=w.id, name="Portugal", valid_from=date(1900, 1, 1), popularity=0)
    db.add(c); db.flush(); return c


def clubs(db, w, c, n):
    rows = []
    for i in range(n):
        club = Club(world_id=w.id, country_id=c.id, name=f"Club {i}", founded=date(1900, 1, 1))
        db.add(club); rows.append(club)
    db.flush(); return rows


def test_prevents_league_with_fewer_than_8_clubs():
    db = session(); w = world(db); c = country(db, w); clubs(db, w, c, 7)
    SimulationEngine(db, w).ensure_competitions()
    assert db.scalars(select(Competition)).all() == []


def test_creates_league_with_8_eligible_clubs():
    db = session(); w = world(db); c = country(db, w); clubs(db, w, c, 8)
    SimulationEngine(db, w).ensure_competitions(); db.flush()
    comp = db.scalar(select(Competition))
    assert comp is not None
    assert comp.club_count == 8


def test_calculates_match_count_and_caps_each_club_at_36_games():
    db = session(); w = world(db); c = country(db, w); created = clubs(db, w, c, 20)
    e = SimulationEngine(db, w); e.ensure_competitions(); db.flush(); e.play_matches()
    season = db.scalar(select(Season))
    matches = db.scalars(select(Match).where(Match.season_id == season.id)).all()
    assert len(matches) == (20 * 19) // 2
    for club in created:
        count = sum(1 for m in matches if club.id in (m.home_club_id, m.away_club_id))
        assert count <= 36


def test_prevents_duplicate_matches_in_schedule():
    db = session(); w = world(db); c = country(db, w); clubs(db, w, c, 8)
    e = SimulationEngine(db, w); e.ensure_competitions(); db.flush(); e.play_matches(); e.play_matches()
    matches = db.scalars(select(Match)).all()
    keys = {(m.home_club_id, m.away_club_id, m.played_on) for m in matches}
    assert len(keys) == len(matches)


def test_generates_standings():
    db = session(); w = world(db, date(1900, 10, 1)); c = country(db, w); clubs(db, w, c, 8)
    e = SimulationEngine(db, w); e.ensure_competitions(); db.flush(); e.play_matches(); db.flush(); e.update_standings(); db.flush()
    standings = db.scalars(select(Standing)).all()
    assert standings
    assert all(s.played >= 0 and s.points >= 0 for s in standings)


def test_no_uefa_ranking_before_historical_start():
    db = session(); w = world(db); country(db, w)
    e = SimulationEngine(db, w); e.update_coefficients()
    assert db.scalars(select(ClubCoefficient)).all() == []
    assert db.scalars(select(CountryCoefficient)).all() == []


def test_creates_club_and_country_coefficients_and_historical_ranking():
    db = session(); w = world(db, date(1956, 10, 1)); c = country(db, w); c2 = Country(world_id=w.id, name="England", valid_from=date(1900, 1, 1)); db.add(c2); db.flush()
    a, b = clubs(db, w, c, 1)[0], clubs(db, w, c2, 1)[0]
    db.add(HistoricalCompetitionRule(scope="international", name="European Cup", valid_from=date(1955, 9, 1), international=True))
    comp = Competition(world_id=w.id, name="European Cup", valid_from=date(1955, 9, 1), international=True, format="knockout")
    db.add(comp); db.flush()
    season = Season(competition_id=comp.id, start_date=date(1956, 9, 1), end_date=date(1957, 6, 30)); db.add(season); db.flush()
    db.add(Match(world_id=w.id, competition_id=comp.id, season_id=season.id, played_on=w.current_date, home_club_id=a.id, away_club_id=b.id, home_goals=2, away_goals=1, played=True))
    db.flush()
    SimulationEngine(db, w).update_coefficients(); db.flush()
    club_ranking = db.scalars(select(ClubCoefficient).where(ClubCoefficient.season_year == 1956).order_by(ClubCoefficient.coefficient.desc())).all()
    country_ranking = db.scalars(select(CountryCoefficient).where(CountryCoefficient.season_year == 1956).order_by(CountryCoefficient.coefficient.desc())).all()
    assert club_ranking and club_ranking[0].club_id == a.id
    assert country_ranking and country_ranking[0].country_id == c.id


def test_simulation_continues_after_2026():
    db = session(); w = world(db, date(2026, 12, 1))
    SimulationEngine(db, w).run_month()
    assert w.current_date == date(2027, 1, 1)


def scheduled_world(db, current_date=date(1900, 9, 1), club_count=8):
    w = world(db, current_date); c = country(db, w); created = clubs(db, w, c, club_count)
    e = SimulationEngine(db, w); e.ensure_competitions(); db.flush(); e.play_matches(); db.flush()
    return w, c, created, db.scalar(select(Season))


def test_select_and_persist_player_club_on_world():
    db = session(); w = world(db); c = country(db, w); selected = clubs(db, w, c, 1)[0]
    w.player_club_id = selected.id; db.commit()
    loaded = db.get(GameWorld, w.id)
    assert loaded.player_club_id == selected.id


def test_schedule_uses_concrete_dates_and_finds_next_match():
    db = session(); w, _c, created, _season = scheduled_world(db)
    w.player_club_id = created[0].id; db.flush()
    matches = db.scalars(select(Match).where(Match.world_id == w.id).order_by(Match.played_on)).all()
    assert matches
    assert any(m.played_on.day != 1 for m in matches)
    next_match = SimulationEngine(db, w).next_match_for_player_club()
    assert next_match is not None
    assert created[0].id in (next_match.home_club_id, next_match.away_club_id)
    assert next_match.played_on >= w.current_date


def test_advance_to_next_match_stops_before_match_date_and_does_not_play_it():
    db = session(); w, _c, created, _season = scheduled_world(db)
    w.player_club_id = created[0].id; db.flush()
    e = SimulationEngine(db, w)
    next_match = e.next_match_for_player_club()
    match_date = next_match.played_on
    returned = e.advance_to_next_match()
    assert returned.id == next_match.id
    assert w.current_date == match_date - __import__('datetime').timedelta(days=1)
    assert w.current_date < match_date
    assert db.get(Match, next_match.id).played is False


def test_match_calendar_still_respects_duplicate_and_36_game_rules_after_2026():
    db = session(); w, _c, created, season = scheduled_world(db, date(2027, 9, 1), 20)
    matches = db.scalars(select(Match).where(Match.season_id == season.id)).all()
    keys = {(m.home_club_id, m.away_club_id, m.played_on) for m in matches}
    assert len(keys) == len(matches)
    for club in created:
        count = sum(1 for m in matches if club.id in (m.home_club_id, m.away_club_id))
        assert count <= 36
