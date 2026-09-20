import multiprocessing
import random
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Type

from tqdm import tqdm

from monopoly.analytics import Analyzer
from monopoly.core.game import monopoly_game
from monopoly.log import Log
from monopoly.log_settings import LogSettings
from settings import SimulationSettings


def _init_worker(lock):
    """Initialize each worker process with the shared log lock."""
    Log.set_lock(lock)


def run_simulation(config: Type[SimulationSettings]) -> None:
    """Simulate N games in parallel, then print an analysis."""
    LogSettings.init_logs()

    # Create a managed lock for cross-process log safety (works on Windows 'spawn')
    manager = multiprocessing.Manager()
    lock = manager.Lock()
    Log.set_lock(lock)  # Also set for the main process

    master_rng = random.Random(config.seed)
    game_seed_pairs = [(i + 1, master_rng.getrandbits(32)) for i in range(config.n_games)]

    with ProcessPoolExecutor(max_workers=config.multi_process, initializer=_init_worker, initargs=(lock,)) as executor:
        futures = [executor.submit(monopoly_game, item) for item in game_seed_pairs]
        for f in tqdm(as_completed(futures), total=len(futures), desc="Simulating Monopoly games"):
            f.result()

    Analyzer().run_all()


if __name__ == "__main__":
    run_simulation(SimulationSettings)
