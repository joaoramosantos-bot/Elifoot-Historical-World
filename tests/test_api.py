from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app


def test_new_world_starts_on_september_1900_and_advances_to_october():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            create_response = client.post("/world", json={"name": "Teste", "seed": 1900})
            assert create_response.status_code == 200
            world = create_response.json()
            assert world["current_date"] == date(1900, 9, 1).isoformat()

            advance_response = client.post(f"/world/{world['id']}/advance-month")
            assert advance_response.status_code == 200
            assert advance_response.json()["current_date"] == date(1900, 10, 1).isoformat()
    finally:
        app.dependency_overrides.clear()


def test_player_club_and_next_match_api():
    from uuid import uuid4
    from app.models import Club, Country, GameWorld
    from app.engine import SimulationEngine

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        db = TestingSessionLocal()
        w = GameWorld(id=str(uuid4()), name="API", current_date=date(1900, 9, 1), seed=1, created_at=date(1900, 9, 1))
        db.add(w); db.flush()
        c = Country(world_id=w.id, name="Portugal", valid_from=date(1900, 1, 1), popularity=0)
        db.add(c); db.flush()
        made = []
        for i in range(8):
            club = Club(world_id=w.id, country_id=c.id, name=f"Club {i}", founded=date(1900, 1, 1))
            db.add(club); made.append(club)
        db.flush()
        SimulationEngine(db, w).ensure_competitions(); db.flush(); SimulationEngine(db, w).play_matches(); db.commit()
        world_id, club_id = w.id, made[0].id
        db.close()
        with TestClient(app) as client:
            selected = client.post(f"/world/{world_id}/player-club", json={"club_id": club_id})
            assert selected.status_code == 200
            assert selected.json()["id"] == club_id
            loaded = client.get(f"/world/{world_id}/player-club")
            assert loaded.status_code == 200
            assert loaded.json()["id"] == club_id
            next_response = client.get(f"/world/{world_id}/next-match")
            assert next_response.status_code == 200
            next_match = next_response.json()["next_match"]
            assert next_match is not None
            advance = client.post(f"/world/{world_id}/advance-to-next-match")
            assert advance.status_code == 200
            assert advance.json()["current_date"] < next_match["played_on"]
            assert advance.json()["next_match"]["id"] == next_match["id"]
    finally:
        app.dependency_overrides.clear()
