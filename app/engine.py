from datetime import date
import random
from sqlalchemy import select
from sqlalchemy.orm import Session
from .calendar import advance_month
from .models import *

POSITIONS = ["GK", "DF", "MF", "FW"]
FIRST = ["João", "Manuel", "António", "José", "Carlos", "Francisco", "Henrique", "Luís"]
LAST = ["Silva", "Santos", "Costa", "Pereira", "Oliveira", "Ferreira", "Martins", "Almeida"]

class SimulationEngine:
    def __init__(self, db: Session, world: GameWorld):
        self.db = db
        self.world = world
        self.rng = random.Random(world.seed + world.current_date.year * 100 + world.current_date.month)

    def run_month(self):
        self.world.current_date = advance_month(self.world.current_date)
        self.process_historical_events()
        self.age_and_develop_players()
        self.process_injuries()
        self.process_contracts()
        self.process_transfers()
        self.ensure_competitions()
        self.play_matches()
        self.update_standings()
        self.process_finances()
        self.generate_players_if_needed()
        self.process_retirements()
        self.process_club_lifecycle()
        self.db.commit()
        return self.world

    def process_historical_events(self):
        if self.world.current_date == date(1900, 10, 1):
            self.db.add(HistoricalEvent(
                world_id=self.world.id, event_date=self.world.current_date,
                event_type="world", title="Primeiro mês da simulação",
                description="A simulação histórica entrou em Outubro de 1900."
            ))

    def player_rating(self, p):
        vals = [p.technique,p.passing,p.finishing,p.speed,p.strength,p.stamina,
                p.intelligence,p.positioning,p.discipline,p.mentality]
        return sum(vals)/len(vals) * (0.7 + p.form/200) * (0.7 + p.morale/200) * (0.7 + p.fitness/300)

    def age_and_develop_players(self):
        players = self.db.scalars(select(Player).where(
            Player.world_id == self.world.id, Player.retired == False)).all()
        for p in players:
            age = self.world.current_date.year - p.birth_date.year
            average = self.player_rating(p)
            if 15 <= age <= 28:
                growth = max(0, p.potential - average) * 0.003
                for attr in ("technique","passing","finishing","speed","strength",
                             "stamina","intelligence","positioning","discipline","mentality"):
                    setattr(p, attr, min(100, getattr(p, attr) + growth))
            if age > 30:
                p.speed = max(1, p.speed - 0.08)
                p.stamina = max(1, p.stamina - 0.08)
            p.market_value = max(0, self.player_rating(p) ** 2 * max(1, 18 - abs(age - 25)) / 50)

    def process_injuries(self):
        players = self.db.scalars(select(Player).where(
            Player.world_id == self.world.id, Player.retired == False)).all()
        for p in players:
            if p.injured:
                if self.rng.random() < 0.35:
                    p.injured, p.fitness = False, 100
            elif self.rng.random() < 0.01:
                p.injured, p.fitness = True, 60
            else:
                p.fitness = min(100, p.fitness + 2)

    def process_contracts(self):
        expired = self.db.scalars(select(Contract).where(
            Contract.end_date < self.world.current_date)).all()
        for c in expired:
            p = self.db.get(Player, c.player_id)
            if p and p.club_id == c.club_id:
                p.club_id = None
            self.db.delete(c)

    def process_transfers(self):
        pass

    def ensure_competitions(self):
        countries = self.db.scalars(select(Country).where(
            Country.world_id == self.world.id,
            Country.valid_from <= self.world.current_date)).all()
        for country in countries:
            exists = self.db.scalar(select(Competition).where(
                Competition.world_id == self.world.id,
                Competition.country_id == country.id,
                Competition.valid_from <= self.world.current_date,
                Competition.valid_to.is_(None)))
            if not exists:
                clubs = self.db.scalars(select(Club).where(
                    Club.country_id == country.id, Club.active == True)).all()
                if clubs:
                    self.db.add(Competition(
                        world_id=self.world.id, country_id=country.id,
                        name=f"Campeonato Nacional de {country.name}",
                        valid_from=self.world.current_date,
                        format="league", club_count=max(2, len(clubs)),
                        division_level=1
                    ))

    def club_strength(self, club):
        players = self.db.scalars(select(Player).where(
            Player.club_id == club.id, Player.retired == False)).all()
        if not players:
            return max(5, club.strength)
        return sum(self.player_rating(p) * (0.5 if p.injured else 1)
                   for p in players) / len(players) + club.reputation * .15

    def simulate_match(self, home, away):
        hf, af = self.club_strength(home), self.club_strength(away)
        home_adv = 1.08
        xh = max(0.15, 1.15 * (hf * home_adv) / max(1, af) + self.rng.uniform(-0.35, 0.35))
        xa = max(0.10, 1.05 * af / max(1, hf * home_adv) + self.rng.uniform(-0.35, 0.35))
        return min(8, int(xh)), min(8, int(xa))

    def play_matches(self):
        competitions = self.db.scalars(select(Competition).where(
            Competition.world_id == self.world.id,
            Competition.valid_from <= self.world.current_date,
            Competition.valid_to.is_(None))).all()
        for comp in competitions:
            clubs = self.db.scalars(select(Club).where(
                Club.country_id == comp.country_id, Club.active == True,
                Club.division_level == comp.division_level)).all()
            if len(clubs) < 2:
                continue
            season = self.db.scalar(select(Season).where(
                Season.competition_id == comp.id,
                Season.start_date <= self.world.current_date,
                Season.end_date >= self.world.current_date))
            if not season:
                season = Season(
                    competition_id=comp.id,
                    start_date=date(self.world.current_date.year, 9, 1),
                    end_date=date(self.world.current_date.year + 1, 6, 30)
                )
                self.db.add(season)
                self.db.flush()
            offset = self.world.current_date.month - 9
            for i in range(0, len(clubs)-1, 2):
                h = clubs[(i + offset) % len(clubs)]
                a = clubs[(i + 1 + offset) % len(clubs)]
                if h.id == a.id:
                    continue
                existing = self.db.scalar(select(Match).where(
                    Match.competition_id == comp.id,
                    Match.played_on == self.world.current_date,
                    Match.home_club_id == h.id,
                    Match.away_club_id == a.id))
                if existing:
                    continue
                hg, ag = self.simulate_match(h, a)
                self.db.add(Match(
                    world_id=self.world.id, competition_id=comp.id,
                    season_id=season.id, played_on=self.world.current_date,
                    home_club_id=h.id, away_club_id=a.id,
                    home_goals=hg, away_goals=ag, played=True))

    def update_standings(self):
        pass

    def process_finances(self):
        clubs = self.db.scalars(select(Club).where(
            Club.world_id == self.world.id, Club.active == True)).all()
        for club in clubs:
            players = self.db.scalars(select(Player).where(
                Player.club_id == club.id, Player.retired == False)).all()
            wages = sum(p.salary for p in players)
            attendance = max(50, int(club.stadium_capacity * (0.25 + club.reputation/200)))
            ticket_price = max(0.05, 0.02 * (1 + self.world.current_date.year/100))
            gate = attendance * ticket_price
            club.cash += gate - wages - club.stadium_capacity * 0.0001
            self.db.add(FinancialTransaction(
                world_id=self.world.id, club_id=club.id,
                transaction_date=self.world.current_date,
                category="gate", amount=gate,
                description="Receita de bilheteira"))
            self.db.add(FinancialTransaction(
                world_id=self.world.id, club_id=club.id,
                transaction_date=self.world.current_date,
                category="wages", amount=-wages,
                description="Salários"))

    def generate_players_if_needed(self):
        countries = self.db.scalars(select(Country).where(Country.world_id == self.world.id)).all()
        clubs = self.db.scalars(select(Club).where(
            Club.world_id == self.world.id, Club.active == True)).all()
        target = max(12, len(clubs) * 16)
        current = len(self.db.scalars(select(Player).where(
            Player.world_id == self.world.id, Player.retired == False)).all())
        for _ in range(max(0, target-current)):
            country = self.rng.choice(countries)
            age = self.rng.randint(15, 24)
            birth_year = self.world.current_date.year - age
            p = Player(
                world_id=self.world.id,
                club_id=self.rng.choice(clubs).id if clubs and self.rng.random() < 0.85 else None,
                nationality=country.name,
                name=f"{self.rng.choice(FIRST)} {self.rng.choice(LAST)}",
                birth_date=date(birth_year, self.rng.randint(1,12), self.rng.randint(1,28)),
                position=self.rng.choice(POSITIONS),
                technique=self.rng.uniform(15,40), passing=self.rng.uniform(15,40),
                finishing=self.rng.uniform(15,40), speed=self.rng.uniform(15,40),
                strength=self.rng.uniform(15,40), stamina=self.rng.uniform(15,40),
                intelligence=self.rng.uniform(15,40), positioning=self.rng.uniform(15,40),
                discipline=self.rng.uniform(15,40), mentality=self.rng.uniform(15,40),
                potential=self.rng.uniform(30,75), salary=self.rng.uniform(0.5,5)
            )
            p.market_value = self.player_rating(p)
            self.db.add(p)

    def process_retirements(self):
        players = self.db.scalars(select(Player).where(
            Player.world_id == self.world.id, Player.retired == False)).all()
        for p in players:
            age = self.world.current_date.year - p.birth_date.year
            if age >= 36 and self.rng.random() < min(0.2, 0.03 + (age-36)*0.02):
                p.retired = True
                p.club_id = None

    def process_club_lifecycle(self):
        clubs = self.db.scalars(select(Club).where(
            Club.world_id == self.world.id, Club.active == True)).all()
        for club in clubs:
            if club.cash < -500 and self.rng.random() < 0.05:
                club.active = False
                club.dissolved = self.world.current_date
                self.db.add(HistoricalEvent(
                    world_id=self.world.id,
                    event_date=self.world.current_date,
                    event_type="club_dissolution",
                    title=f"{club.name} desapareceu",
                    description="O clube entrou em insolvência e deixou de competir."
                ))
