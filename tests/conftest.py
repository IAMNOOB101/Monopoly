"""Shared fixtures for Monopoly test suite."""
import sys
from pathlib import Path

import pytest

# Add project root to path so imports work
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from monopoly.core.board import Board
from monopoly.core.cell import Property
from monopoly.core.dice import Dice
from monopoly.core.player import Player
from monopoly.log import Log
from settings import GameSettings, GameMechanics, StandardPlayerSettings, HeroPlayerSettings


class NullLog:
    """A no-op log for testing — avoids file I/O."""
    def add(self, data):
        pass
    def save(self):
        pass
    def reset(self, first_line=""):
        pass


@pytest.fixture
def null_log():
    """A log that discards everything (no file I/O in tests)."""
    return NullLog()


@pytest.fixture
def board():
    """A fresh Monopoly board."""
    return Board(GameSettings)


@pytest.fixture
def dice(null_log):
    """A seeded dice for reproducible tests."""
    return Dice(42, GameMechanics.dice_count, GameMechanics.dice_sides, null_log)


@pytest.fixture
def standard_player():
    """A standard player with $1500."""
    p = Player("TestPlayer", StandardPlayerSettings)
    p.money = 1500
    return p


@pytest.fixture
def hero_player():
    """The hero (experimental) player with $1500."""
    p = Player("Hero", HeroPlayerSettings)
    p.money = 1500
    return p


@pytest.fixture
def four_players():
    """Four players with $1500 each, ready for a game."""
    players = [
        Player("Hero", HeroPlayerSettings),
        Player("Alice", StandardPlayerSettings),
        Player("Bob", StandardPlayerSettings),
        Player("Charly", StandardPlayerSettings),
    ]
    for p in players:
        p.money = 1500
    return players


@pytest.fixture
def player_with_monopoly(board):
    """A player who owns all Brown properties (Mediterranean + Baltic)."""
    p = Player("MonopolyPlayer", StandardPlayerSettings)
    p.money = 1500
    # Brown group: cells 1 and 3
    for idx in [1, 3]:
        cell = board.cells[idx]
        cell.owner = p
        p.owned.append(cell)
    board.recalculate_monopoly_multipliers(board.cells[1])
    return p
