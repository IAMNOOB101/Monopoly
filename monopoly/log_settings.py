from pathlib import Path

from monopoly.log import Log

project_root = Path(__file__).resolve().parent
results_dir = project_root.parent / "results"


class LogSettings:
    KEEP_GAME_LOG = True
    EVENTS_LOG_PATH = results_dir / "events.log"
    BANKRUPTCIES_PATH = results_dir / "bankruptcies.tsv"
    NETWORTH_LOG_PATH = results_dir / "networth.tsv"
    LANDINGS_LOG_PATH = results_dir / "landings.tsv"
    PLOTS_DIR = results_dir / "plots"

    @classmethod
    def init_logs(cls):
        """Initiate & reset both logs; return (events_log, bankruptcies_log)."""

        # Ensure results and plots directories exist
        results_dir.mkdir(exist_ok=True)
        cls.PLOTS_DIR.mkdir(exist_ok=True)

        # 1) events log
        events_log = Log(cls.EVENTS_LOG_PATH, disabled=not cls.KEEP_GAME_LOG)
        events_log.reset("Events log")

        # 2) bankruptcies summary log
        bankruptcies_log = Log(cls.BANKRUPTCIES_PATH)
        bankruptcies_log.reset("game_number\tplayer_bankrupt\tturn")

        # 3) net worth tracking log
        networth_log = Log(cls.NETWORTH_LOG_PATH)
        networth_log.reset("game_number\tturn\tplayer\tnet_worth")

        # 4) landings tracking log
        landings_log = Log(cls.LANDINGS_LOG_PATH)
        landings_log.reset("game_number\tturn\tplayer\tposition")

        return events_log, bankruptcies_log
