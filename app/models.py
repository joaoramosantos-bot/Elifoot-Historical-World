from datetime import date
from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class GameWorld(Base):
    __tablename__ = "game_worlds"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    current_date: Mapped[date] = mapped_column(Date, nullable=False)
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[date] = mapped_column(Date, nullable=False)
    player_club_id: Mapped[int | None] = mapped_column(ForeignKey("clubs.id"), nullable=True)

class Country(Base):
    __tablename__ = "countries"
    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[str] = mapped_column(ForeignKey("game_worlds.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    organisation: Mapped[float] = mapped_column(Float, default=10)
    professionalism: Mapped[float] = mapped_column(Float, default=0)
    infrastructure: Mapped[float] = mapped_column(Float, default=10)
    popularity: Mapped[float] = mapped_column(Float, default=10)
    finance: Mapped[float] = mapped_column(Float, default=10)
    competition_development: Mapped[float] = mapped_column(Float, default=10)
    player_quality: Mapped[float] = mapped_column(Float, default=10)
    manager_quality: Mapped[float] = mapped_column(Float, default=10)

class City(Base):
    __tablename__ = "cities"
    id: Mapped[int] = mapped_column(primary_key=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)

class Stadium(Base):
    __tablename__ = "stadiums"
    id: Mapped[int] = mapped_column(primary_key=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    capacity: Mapped[int] = mapped_column(Integer, default=500)
    quality: Mapped[float] = mapped_column(Float, default=10)
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)

class Club(Base):
    __tablename__ = "clubs"
    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[str] = mapped_column(ForeignKey("game_worlds.id"), index=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"))
    city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(140))
    founded: Mapped[date] = mapped_column(Date)
    dissolved: Mapped[date | None] = mapped_column(Date, nullable=True)
    division_level: Mapped[int] = mapped_column(Integer, default=1)
    professional: Mapped[bool] = mapped_column(Boolean, default=False)
    strength: Mapped[float] = mapped_column(Float, default=20)
    reputation: Mapped[float] = mapped_column(Float, default=10)
    cash: Mapped[float] = mapped_column(Float, default=1000)
    debt: Mapped[float] = mapped_column(Float, default=0)
    stadium_capacity: Mapped[int] = mapped_column(Integer, default=500)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class Player(Base):
    __tablename__ = "players"
    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[str] = mapped_column(ForeignKey("game_worlds.id"), index=True)
    club_id: Mapped[int | None] = mapped_column(ForeignKey("clubs.id"), nullable=True)
    nationality: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(140))
    birth_date: Mapped[date] = mapped_column(Date)
    position: Mapped[str] = mapped_column(String(20))
    technique: Mapped[float] = mapped_column(Float)
    passing: Mapped[float] = mapped_column(Float)
    finishing: Mapped[float] = mapped_column(Float)
    speed: Mapped[float] = mapped_column(Float)
    strength: Mapped[float] = mapped_column(Float)
    stamina: Mapped[float] = mapped_column(Float)
    intelligence: Mapped[float] = mapped_column(Float)
    positioning: Mapped[float] = mapped_column(Float)
    discipline: Mapped[float] = mapped_column(Float)
    mentality: Mapped[float] = mapped_column(Float)
    potential: Mapped[float] = mapped_column(Float)
    form: Mapped[float] = mapped_column(Float, default=50)
    morale: Mapped[float] = mapped_column(Float, default=50)
    fitness: Mapped[float] = mapped_column(Float, default=100)
    injured: Mapped[bool] = mapped_column(Boolean, default=False)
    retired: Mapped[bool] = mapped_column(Boolean, default=False)
    salary: Mapped[float] = mapped_column(Float, default=0)
    market_value: Mapped[float] = mapped_column(Float, default=0)

class Manager(Base):
    __tablename__ = "managers"
    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[str] = mapped_column(ForeignKey("game_worlds.id"), index=True)
    club_id: Mapped[int | None] = mapped_column(ForeignKey("clubs.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(140))
    birth_date: Mapped[date] = mapped_column(Date)
    quality: Mapped[float] = mapped_column(Float, default=20)

class Competition(Base):
    __tablename__ = "competitions"
    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[str] = mapped_column(ForeignKey("game_worlds.id"), index=True)
    country_id: Mapped[int | None] = mapped_column(ForeignKey("countries.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(140))
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    format: Mapped[str] = mapped_column(String(40), default="league")
    club_count: Mapped[int] = mapped_column(Integer, default=8)
    division_level: Mapped[int] = mapped_column(Integer, default=1)
    international: Mapped[bool] = mapped_column(Boolean, default=False)

class Season(Base):
    __tablename__ = "seasons"
    id: Mapped[int] = mapped_column(primary_key=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"), index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="active")

class Match(Base):
    __tablename__ = "matches"
    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[str] = mapped_column(ForeignKey("game_worlds.id"), index=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"))
    season_id: Mapped[int | None] = mapped_column(ForeignKey("seasons.id"), nullable=True)
    played_on: Mapped[date] = mapped_column(Date)
    home_club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id"))
    away_club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id"))
    home_goals: Mapped[int] = mapped_column(Integer, default=0)
    away_goals: Mapped[int] = mapped_column(Integer, default=0)
    played: Mapped[bool] = mapped_column(Boolean, default=False)

class Transfer(Base):
    __tablename__ = "transfers"
    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[str] = mapped_column(ForeignKey("game_worlds.id"), index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    from_club_id: Mapped[int | None] = mapped_column(ForeignKey("clubs.id"), nullable=True)
    to_club_id: Mapped[int | None] = mapped_column(ForeignKey("clubs.id"), nullable=True)
    transfer_date: Mapped[date] = mapped_column(Date)
    fee: Mapped[float] = mapped_column(Float, default=0)

class Contract(Base):
    __tablename__ = "contracts"
    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id"))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    salary: Mapped[float] = mapped_column(Float)

class FinancialTransaction(Base):
    __tablename__ = "financial_transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[str] = mapped_column(ForeignKey("game_worlds.id"), index=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id"))
    transaction_date: Mapped[date] = mapped_column(Date)
    category: Mapped[str] = mapped_column(String(50))
    amount: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(Text, default="")

class HistoricalCompetitionRule(Base):
    __tablename__ = "historical_competition_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    scope: Mapped[str] = mapped_column(String(40), default="national")
    country_id: Mapped[int | None] = mapped_column(ForeignKey("countries.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(140))
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    format: Mapped[str] = mapped_column(String(40), default="league")
    min_clubs: Mapped[int] = mapped_column(Integer, default=8)
    max_clubs: Mapped[int] = mapped_column(Integer, default=20)
    matches_per_opponent: Mapped[int] = mapped_column(Integer, default=2)
    season_start_month: Mapped[int] = mapped_column(Integer, default=9)
    season_end_month: Mapped[int] = mapped_column(Integer, default=6)
    international: Mapped[bool] = mapped_column(Boolean, default=False)

class Standing(Base):
    __tablename__ = "standings"
    id: Mapped[int] = mapped_column(primary_key=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"), index=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id"), index=True)
    played: Mapped[int] = mapped_column(Integer, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    draws: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    goals_for: Mapped[int] = mapped_column(Integer, default=0)
    goals_against: Mapped[int] = mapped_column(Integer, default=0)
    goal_difference: Mapped[int] = mapped_column(Integer, default=0)
    points: Mapped[int] = mapped_column(Integer, default=0)

class ClubCoefficient(Base):
    __tablename__ = "club_coefficients"
    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[str] = mapped_column(ForeignKey("game_worlds.id"), index=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id"), index=True)
    season_year: Mapped[int] = mapped_column(Integer, index=True)
    participation_points: Mapped[float] = mapped_column(Float, default=0)
    result_points: Mapped[float] = mapped_column(Float, default=0)
    progression_points: Mapped[float] = mapped_column(Float, default=0)
    coefficient: Mapped[float] = mapped_column(Float, default=0)

class CountryCoefficient(Base):
    __tablename__ = "country_coefficients"
    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[str] = mapped_column(ForeignKey("game_worlds.id"), index=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), index=True)
    season_year: Mapped[int] = mapped_column(Integer, index=True)
    coefficient: Mapped[float] = mapped_column(Float, default=0)
    club_count: Mapped[int] = mapped_column(Integer, default=0)

class HistoricalEvent(Base):
    __tablename__ = "historical_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[str] = mapped_column(ForeignKey("game_worlds.id"), index=True)
    event_date: Mapped[date] = mapped_column(Date)
    event_type: Mapped[str] = mapped_column(String(60))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
