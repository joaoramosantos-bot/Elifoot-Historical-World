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
