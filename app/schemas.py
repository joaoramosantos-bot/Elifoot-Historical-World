from datetime import date
from pydantic import BaseModel, ConfigDict

class WorldCreate(BaseModel):
    name: str = "Elifoot Historical World"
    seed: int = 1900

class WorldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    current_date: date
    seed: int


class PlayerClubSelect(BaseModel):
    club_id: int
