from datetime import date, timedelta

from sqlalchemy import select

from .engine import SimulationEngine
from .models import Competition, Club, Match, Season


class WeeklySimulationEngine(SimulationEngine):
    """Advance the world by one week with round-robin scheduling."""

    def play_matches(self):
        competitions = self.db.scalars(select(Competition).where(
            Competition.world_id == self.world.id,
            Competition.valid_from <= self.world.current_date,
            Competition.valid_to.is_(None),
        )).all()

        for competition in competitions:
            clubs = self.db.scalars(select(Club).where(
                Club.world_id == self.world.id,
                Club.country_id == competition.country_id,
                Club.division_level == competition.division_level,
                Club.active.is_(True),
            ).order_by(Club.id)).all()

            if len(clubs) < 2:
                continue

            season = self.db.scalar(select(Season).where(
                Season.competition_id == competition.id,
                Season.start_date <= self.world.current_date,
                Season.end_date >= self.world.current_date,
            ))
            if not season:
                season = Season(
                    competition_id=competition.id,
                    start_date=date(self.world.current_date.year, 9, 1),
                    end_date=date(self.world.current_date.year + 1, 6, 30),
                )
                self.db.add(season)
                self.db.flush()

            # Circle method: each club plays exactly once per round;
            # with an odd number of clubs, one club has a rotating bye.
            rotation = list(clubs)
            if len(rotation) % 2:
                rotation.append(None)

            round_number = max(0, (self.world.current_date - season.start_date).days // 7)
            rounds = len(rotation) - 1
            current_round = round_number % rounds

            for _ in range(current_round):
                rotation = [rotation[0], rotation[-1], *rotation[1:-1]]

            for index in range(len(rotation) // 2):
                home = rotation[index]
                away = rotation[-index - 1]
                if home is None or away is None:
                    continue

                existing = self.db.scalar(select(Match).where(
                    Match.competition_id == competition.id,
                    Match.played_on == self.world.current_date,
                    Match.home_club_id.in_([home.id, away.id]),
                    Match.away_club_id.in_([home.id, away.id]),
                ))
                if existing:
                    continue

                home_goals, away_goals = self.simulate_match(home, away)
                self.db.add(Match(
                    world_id=self.world.id,
                    competition_id=competition.id,
                    season_id=season.id,
                    played_on=self.world.current_date,
                    home_club_id=home.id,
                    away_club_id=away.id,
                    home_goals=home_goals,
                    away_goals=away_goals,
                    played=True,
                ))

    def run_week(self):
        self.world.current_date = self.world.current_date + timedelta(days=7)
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
