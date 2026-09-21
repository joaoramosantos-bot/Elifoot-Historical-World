from datetime import timedelta

from .engine import SimulationEngine


class WeeklySimulationEngine(SimulationEngine):
    """Advance the world by one week while running the complete simulation pipeline."""

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
