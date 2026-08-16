from datetime import date
from uuid import uuid4
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from .db import Base, engine, get_db
from .models import *
from .schemas import WorldCreate, WorldOut
from .engine import SimulationEngine

app = FastAPI(title="Elifoot Historical World", version="0.1.0")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(engine)

@app.post("/world", response_model=WorldOut)
def create_world(payload: WorldCreate, db: Session = Depends(get_db)):
    world = GameWorld(
        id=str(uuid4()), name=payload.name,
        current_date=date(1900,9,1), seed=payload.seed,
        created_at=date.today()
    )
    db.add(world)
    db.commit()
    db.refresh(world)
    return world

@app.get("/world/{id}", response_model=WorldOut)
def get_world(id: str, db: Session = Depends(get_db)):
    world = db.get(GameWorld, id)
    if not world:
        raise HTTPException(404, "World not found")
    return world

@app.post("/world/{id}/advance-month", response_model=WorldOut)
def advance(id: str, db: Session = Depends(get_db)):
    world = db.get(GameWorld, id)
    if not world:
        raise HTTPException(404, "World not found")
    SimulationEngine(db, world).run_month()
    db.refresh(world)
    return world

def rows(model, world_id, db):
    result = []
    for r in db.scalars(select(model).where(model.world_id == world_id)).all():
        data = {k:v for k,v in r.__dict__.items() if k != "_sa_instance_state"}
        result.append(data)
    return result

@app.get("/world/{id}/clubs")
def clubs(id: str, db: Session = Depends(get_db)):
    if not db.get(GameWorld,id): raise HTTPException(404,"World not found")
    return rows(Club,id,db)

@app.get("/world/{id}/players")
def players(id: str, db: Session = Depends(get_db)):
    if not db.get(GameWorld,id): raise HTTPException(404,"World not found")
    return rows(Player,id,db)

@app.get("/world/{id}/competitions")
def competitions(id: str, db: Session = Depends(get_db)):
    if not db.get(GameWorld,id): raise HTTPException(404,"World not found")
    return rows(Competition,id,db)

@app.get("/world/{id}/matches")
def matches(id: str, db: Session = Depends(get_db)):
    if not db.get(GameWorld,id): raise HTTPException(404,"World not found")
    return rows(Match,id,db)

@app.get("/world/{id}/history")
def history(id: str, db: Session = Depends(get_db)):
    if not db.get(GameWorld,id): raise HTTPException(404,"World not found")
    return rows(HistoricalEvent,id,db)

@app.get("/world/{id}/standings")
def standings(id: str, db: Session = Depends(get_db)):
    if not db.get(GameWorld,id): raise HTTPException(404,"World not found")
    return [
        {k:v for k,v in r.__dict__.items() if k != "_sa_instance_state"}
        for r in db.scalars(select(Standing).join(Season, Standing.season_id == Season.id).join(Competition, Season.competition_id == Competition.id).where(Competition.world_id == id).order_by(Standing.points.desc(), Standing.goal_difference.desc())).all()
    ]

@app.get("/world/{id}/rankings/clubs")
def club_rankings(id: str, season_year: int | None = None, db: Session = Depends(get_db)):
    if not db.get(GameWorld,id): raise HTTPException(404,"World not found")
    query = select(ClubCoefficient).where(ClubCoefficient.world_id == id)
    if season_year is not None:
        query = query.where(ClubCoefficient.season_year == season_year)
    return [{k:v for k,v in r.__dict__.items() if k != "_sa_instance_state"}
            for r in db.scalars(query.order_by(ClubCoefficient.coefficient.desc())).all()]

@app.get("/world/{id}/rankings/countries")
def country_rankings(id: str, season_year: int | None = None, db: Session = Depends(get_db)):
    if not db.get(GameWorld,id): raise HTTPException(404,"World not found")
    query = select(CountryCoefficient).where(CountryCoefficient.world_id == id)
    if season_year is not None:
        query = query.where(CountryCoefficient.season_year == season_year)
    return [{k:v for k,v in r.__dict__.items() if k != "_sa_instance_state"}
            for r in db.scalars(query.order_by(CountryCoefficient.coefficient.desc())).all()]
