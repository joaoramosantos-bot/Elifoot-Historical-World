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
        self.process_club_births()
        self.ensure_competitions()
        self.play_matches()
        self.update_standings()
        self.update_coefficients()
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

    def eligible_clubs(self, country, division_level=1):
        return self.db.scalars(select(Club).where(
            Club.world_id == self.world.id,
            Club.country_id == country.id,
            Club.division_level == division_level,
            Club.active == True,
            Club.founded <= self.world.current_date
        ).order_by(Club.id)).all()

    def competition_rule_for(self, country):
        rule = self.db.scalar(select(HistoricalCompetitionRule).where(
            HistoricalCompetitionRule.scope == "national",
            HistoricalCompetitionRule.country_id == country.id,
            HistoricalCompetitionRule.valid_from <= self.world.current_date,
            (HistoricalCompetitionRule.valid_to.is_(None)) | (HistoricalCompetitionRule.valid_to >= self.world.current_date)
        ).order_by(HistoricalCompetitionRule.valid_from.desc()))
        if rule:
            return rule
        return HistoricalCompetitionRule(
            scope="national", country_id=country.id,
            name=f"Campeonato Nacional de {country.name}",
            valid_from=date(1900, 1, 1), min_clubs=8, max_clubs=20,
            matches_per_opponent=2, season_start_month=9, season_end_month=6
        )

    def process_club_births(self):
        countries = self.db.scalars(select(Country).where(
            Country.world_id == self.world.id,
            Country.valid_from <= self.world.current_date,
            (Country.valid_to.is_(None)) | (Country.valid_to >= self.world.current_date))).all()
        for country in countries:
            active_count = len(self.db.scalars(select(Club).where(
                Club.world_id == self.world.id, Club.country_id == country.id,
                Club.active == True)).all())
            target = min(8, max(0, int(country.popularity // 10) + int((self.world.current_date.year - 1900) // 20)))
            if active_count >= target:
                continue
            club = Club(
                world_id=self.world.id, country_id=country.id, city_id=None,
                name=f"{country.name} Historical Club {active_count + 1}",
                founded=self.world.current_date, division_level=1,
                strength=15 + country.player_quality * 0.4, reputation=10,
                cash=1000 + country.finance * 20, stadium_capacity=500
            )
            self.db.add(club)
            self.db.flush()
            self.db.add(HistoricalEvent(
                world_id=self.world.id, event_date=self.world.current_date,
                event_type="club_foundation", title=f"{club.name} fundado",
                description="Um novo clube nasceu dinamicamente na simulação."
            ))

    def ensure_competitions(self):
        countries = self.db.scalars(select(Country).where(
            Country.world_id == self.world.id,
            Country.valid_from <= self.world.current_date)).all()
        for country in countries:
            clubs = self.eligible_clubs(country, 1)
            rule = self.competition_rule_for(country)
            if len(clubs) < rule.min_clubs:
                continue
            exists = self.db.scalar(select(Competition).where(
                Competition.world_id == self.world.id,
                Competition.country_id == country.id,
                Competition.division_level == 1,
                Competition.valid_from <= self.world.current_date,
                Competition.valid_to.is_(None)))
            if not exists:
                self.db.add(Competition(
                    world_id=self.world.id, country_id=country.id,
                    name=rule.name, valid_from=self.world.current_date,
                    format=rule.format, club_count=min(len(clubs), rule.max_clubs),
                    division_level=1, international=rule.international
                ))
            if len(clubs) >= rule.min_clubs * 2:
                second = self.db.scalar(select(Competition).where(
                    Competition.world_id == self.world.id,
                    Competition.country_id == country.id,
                    Competition.division_level == 2,
                    Competition.valid_to.is_(None)))
                if not second:
                    self.db.add(Competition(
                        world_id=self.world.id, country_id=country.id,
                        name=f"{rule.name} II", valid_from=self.world.current_date,
                        format=rule.format, club_count=min(len(clubs) - rule.min_clubs, rule.max_clubs),
                        division_level=2, international=False
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

    def season_bounds(self, year):
        return date(year, 9, 1), date(year + 1, 6, 30)

    def season_year(self):
        return self.world.current_date.year if self.world.current_date.month >= 9 else self.world.current_date.year - 1

    def league_pairs(self, clubs, matches_per_opponent):
        max_rounds_per_pair = min(4, max(1, matches_per_opponent))
        while (len(clubs) - 1) * max_rounds_per_pair > 36:
            max_rounds_per_pair -= 1
        pairs = []
        for idx, home in enumerate(clubs):
            for away in clubs[idx + 1:]:
                for n in range(max_rounds_per_pair):
                    pairs.append((home, away) if n % 2 == 0 else (away, home))
        return pairs

    def schedule_season_matches(self, comp, season, clubs, rule):
        existing = self.db.scalars(select(Match).where(Match.season_id == season.id)).all()
        existing_keys = {(m.home_club_id, m.away_club_id, m.played_on) for m in existing}
        pairs = self.league_pairs(clubs, rule.matches_per_opponent)
        months = [9, 10, 11, 12, 1, 2, 3, 4, 5, 6]
        for idx, (home, away) in enumerate(pairs):
            month = months[idx % len(months)]
            year = season.start_date.year if month >= 9 else season.end_date.year
            played_on = date(year, month, 1)
            key = (home.id, away.id, played_on)
            reverse_key = (away.id, home.id, played_on)
            if key in existing_keys or reverse_key in existing_keys:
                continue
            self.db.add(Match(
                world_id=self.world.id, competition_id=comp.id, season_id=season.id,
                played_on=played_on, home_club_id=home.id, away_club_id=away.id,
                home_goals=0, away_goals=0, played=False
            ))
            existing_keys.add(key)

    def play_matches(self):
        competitions = self.db.scalars(select(Competition).where(
            Competition.world_id == self.world.id,
            Competition.valid_from <= self.world.current_date,
            Competition.valid_to.is_(None))).all()
        for comp in competitions:
            if comp.format != "league" or comp.international:
                continue
            country = self.db.get(Country, comp.country_id)
            rule = self.competition_rule_for(country)
            clubs = self.eligible_clubs(country, comp.division_level)[:comp.club_count]
            if len(clubs) < rule.min_clubs:
                continue
            start, end = self.season_bounds(self.season_year())
            season = self.db.scalar(select(Season).where(
                Season.competition_id == comp.id,
                Season.start_date == start,
                Season.end_date == end))
            if not season:
                season = Season(competition_id=comp.id, start_date=start, end_date=end)
                self.db.add(season)
                self.db.flush()
                self.schedule_season_matches(comp, season, clubs, rule)
                self.db.flush()
            due = self.db.scalars(select(Match).where(
                Match.season_id == season.id,
                Match.played_on == self.world.current_date,
                Match.played == False)).all()
            for match in due:
                home = self.db.get(Club, match.home_club_id)
                away = self.db.get(Club, match.away_club_id)
                if not home or not away:
                    continue
                match.home_goals, match.away_goals = self.simulate_match(home, away)
                match.played = True

    def update_standings(self):
        seasons = self.db.scalars(select(Season).where(
            Season.start_date <= self.world.current_date,
            Season.end_date >= self.world.current_date)).all()
        for season in seasons:
            for old in self.db.scalars(select(Standing).where(Standing.season_id == season.id)).all():
                self.db.delete(old)
            rows = {}
            matches = self.db.scalars(select(Match).where(
                Match.season_id == season.id, Match.played == True)).all()
            for match in matches:
                for club_id in (match.home_club_id, match.away_club_id):
                    rows.setdefault(club_id, dict(played=0, wins=0, draws=0, losses=0, goals_for=0, goals_against=0, points=0))
                home = rows[match.home_club_id]
                away = rows[match.away_club_id]
                home["played"] += 1; away["played"] += 1
                home["goals_for"] += match.home_goals; home["goals_against"] += match.away_goals
                away["goals_for"] += match.away_goals; away["goals_against"] += match.home_goals
                if match.home_goals > match.away_goals:
                    home["wins"] += 1; home["points"] += 3; away["losses"] += 1
                elif match.home_goals < match.away_goals:
                    away["wins"] += 1; away["points"] += 3; home["losses"] += 1
                else:
                    home["draws"] += 1; away["draws"] += 1; home["points"] += 1; away["points"] += 1
            for club_id, row in rows.items():
                self.db.add(Standing(
                    season_id=season.id, club_id=club_id,
                    goal_difference=row["goals_for"] - row["goals_against"], **row
                ))

    def european_competitions_started(self):
        return self.db.scalar(select(HistoricalCompetitionRule).where(
            HistoricalCompetitionRule.scope == "international",
            HistoricalCompetitionRule.valid_from <= self.world.current_date,
            HistoricalCompetitionRule.international == True)) is not None

    def update_coefficients(self):
        if not self.european_competitions_started():
            return
        season_year = self.season_year()
        international_matches = self.db.scalars(select(Match).join(Competition, Match.competition_id == Competition.id).where(
            Match.world_id == self.world.id, Match.played == True, Competition.international == True)).all()
        club_points = {}
        for match in international_matches:
            club_points.setdefault(match.home_club_id, 1.0)
            club_points.setdefault(match.away_club_id, 1.0)
            if match.home_goals > match.away_goals:
                club_points[match.home_club_id] += 2
            elif match.home_goals < match.away_goals:
                club_points[match.away_club_id] += 2
            else:
                club_points[match.home_club_id] += 1
                club_points[match.away_club_id] += 1
        for club_id, points in club_points.items():
            coeff = self.db.scalar(select(ClubCoefficient).where(
                ClubCoefficient.world_id == self.world.id,
                ClubCoefficient.club_id == club_id,
                ClubCoefficient.season_year == season_year))
            if not coeff:
                coeff = ClubCoefficient(world_id=self.world.id, club_id=club_id, season_year=season_year)
                self.db.add(coeff)
            coeff.participation_points = 1
            coeff.result_points = max(0, points - 1)
            coeff.coefficient = points
        countries = {}
        for club_id, points in club_points.items():
            club = self.db.get(Club, club_id)
            if club:
                countries.setdefault(club.country_id, []).append(points)
        for country_id, points in countries.items():
            coeff = self.db.scalar(select(CountryCoefficient).where(
                CountryCoefficient.world_id == self.world.id,
                CountryCoefficient.country_id == country_id,
                CountryCoefficient.season_year == season_year))
            if not coeff:
                coeff = CountryCoefficient(world_id=self.world.id, country_id=country_id, season_year=season_year)
                self.db.add(coeff)
            coeff.club_count = len(points)
            coeff.coefficient = sum(points) / len(points)

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
        if not countries:
            return

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
