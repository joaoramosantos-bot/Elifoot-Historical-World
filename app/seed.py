from datetime import date
from uuid import uuid4
from .db import Base, engine, SessionLocal
from .models import *

def seed():
    Base.metadata.create_all(engine)
    db = SessionLocal()
    world = GameWorld(
        id=str(uuid4()), name="Elifoot Historical World",
        current_date=date(1900,9,1), seed=1900, created_at=date.today()
    )
    db.add(world)
    db.flush()

    pt = Country(world_id=world.id, name="Portugal", valid_from=date(1900,1,1),
        organisation=25, professionalism=2, infrastructure=15, popularity=25,
        finance=10, competition_development=20, player_quality=20, manager_quality=15)
    gb = Country(world_id=world.id, name="England", valid_from=date(1900,1,1),
        organisation=60, professionalism=20, infrastructure=45, popularity=65,
        finance=45, competition_development=60, player_quality=55, manager_quality=50)
    db.add_all([pt, gb])
    db.flush()

    porto = City(country_id=pt.id, name="Porto", valid_from=date(1900,1,1))
    lisboa = City(country_id=pt.id, name="Lisboa", valid_from=date(1900,1,1))
    london = City(country_id=gb.id, name="London", valid_from=date(1900,1,1))
    db.add_all([porto, lisboa, london])
    db.flush()

    clubs = [
        Club(world_id=world.id, country_id=pt.id, city_id=porto.id,
             name="Porto Historical FC", founded=date(1893,1,1), division_level=1,
             strength=30, reputation=25, cash=5000, stadium_capacity=1500),
        Club(world_id=world.id, country_id=pt.id, city_id=lisboa.id,
             name="Lisboa Sporting Club", founded=date(1900,1,1), division_level=1,
             strength=25, reputation=20, cash=4000, stadium_capacity=1200),
        Club(world_id=world.id, country_id=gb.id, city_id=london.id,
             name="London United", founded=date(1890,1,1), division_level=1,
             strength=45, reputation=40, cash=9000, stadium_capacity=4000),
        Club(world_id=world.id, country_id=gb.id, city_id=london.id,
             name="London Athletic", founded=date(1895,1,1), division_level=1,
             strength=40, reputation=35, cash=8000, stadium_capacity=3500)
    ]
    db.add_all(clubs)
    db.flush()

    for c in clubs:
        db.add(Stadium(
            club_id=c.id, name=f"{c.name} Ground",
            capacity=c.stadium_capacity, quality=20, valid_from=c.founded
        ))

    db.commit()
    print(f"World criada: {world.id}")
    db.close()

if __name__ == "__main__":
    seed()
