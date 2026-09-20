""" Event system for structured data collection.
Events are emitted by the game engine and consumed by subscribers
for analytics, logging, and data collection purposes.
"""
from dataclasses import dataclass, field
from typing import List, Callable, Tuple, Optional


# ── Base Event ──────────────────────────────────────────────

@dataclass
class GameEvent:
    """Base class for all game events."""
    game_number: int = 0
    turn: int = 0


# ── Dice & Movement Events ─────────────────────────────────

@dataclass
class DiceRolled(GameEvent):
    player_name: str = ""
    roll: tuple = ()
    total: int = 0
    is_double: bool = False


@dataclass
class PlayerMoved(GameEvent):
    player_name: str = ""
    from_position: int = 0
    to_position: int = 0
    cell_name: str = ""


@dataclass
class SalaryReceived(GameEvent):
    player_name: str = ""
    amount: int = 0


# ── Property Events ─────────────────────────────────────────

@dataclass
class PropertyBought(GameEvent):
    player_name: str = ""
    property_name: str = ""
    price: int = 0


@dataclass
class RentPaid(GameEvent):
    payer: str = ""
    owner: str = ""
    property_name: str = ""
    amount: int = 0


@dataclass
class PropertyMortgaged(GameEvent):
    player_name: str = ""
    property_name: str = ""
    amount: int = 0


@dataclass
class PropertyUnmortgaged(GameEvent):
    player_name: str = ""
    property_name: str = ""
    cost: int = 0


# ── Building Events ─────────────────────────────────────────

@dataclass
class HouseBuilt(GameEvent):
    player_name: str = ""
    property_name: str = ""
    house_number: int = 0
    cost: int = 0


@dataclass
class HotelBuilt(GameEvent):
    player_name: str = ""
    property_name: str = ""
    cost: int = 0


@dataclass
class HouseSold(GameEvent):
    player_name: str = ""
    property_name: str = ""
    proceeds: int = 0


# ── Card Events ─────────────────────────────────────────────

@dataclass
class CardDrawn(GameEvent):
    player_name: str = ""
    deck_type: str = ""  # "Chance" or "Community Chest"
    card_text: str = ""


# ── Jail Events ─────────────────────────────────────────────

@dataclass
class JailEvent(GameEvent):
    player_name: str = ""
    action: str = ""  # "entered", "exited_doubles", "exited_fine", "exited_card", "stayed"


# ── Tax Events ──────────────────────────────────────────────

@dataclass
class TaxPaid(GameEvent):
    player_name: str = ""
    tax_type: str = ""  # "income", "luxury"
    amount: int = 0


# ── Trade Events ────────────────────────────────────────────

@dataclass
class TradeCompleted(GameEvent):
    player_a: str = ""
    player_b: str = ""
    a_gives: List[str] = field(default_factory=list)
    b_gives: List[str] = field(default_factory=list)
    cash_compensation: int = 0  # positive = A receives cash


# ── Auction Events ──────────────────────────────────────────

@dataclass
class AuctionCompleted(GameEvent):
    property_name: str = ""
    winner: str = ""
    winning_bid: int = 0
    num_bidders: int = 0


@dataclass
class AuctionNoBids(GameEvent):
    property_name: str = ""


# ── Bankruptcy Events ───────────────────────────────────────

@dataclass
class PlayerBankrupt(GameEvent):
    player_name: str = ""
    creditor: str = ""  # player name or "bank"


# ── Turn-Level Snapshot ─────────────────────────────────────

@dataclass
class TurnSnapshot(GameEvent):
    """Emitted at the end of each turn with aggregate data."""
    player_net_worths: dict = field(default_factory=dict)  # {player_name: net_worth}
    player_positions: dict = field(default_factory=dict)   # {player_name: position}


# ── Game-Level Events ───────────────────────────────────────

@dataclass
class GameStarted(GameEvent):
    player_names: List[str] = field(default_factory=list)
    seed: int = 0


@dataclass
class GameEnded(GameEvent):
    reason: str = ""  # "winner", "all_rich", "turn_limit"
    survivors: List[str] = field(default_factory=list)


# ── Event Bus ───────────────────────────────────────────────

class EventBus:
    """Simple publish-subscribe event bus for game events."""

    def __init__(self):
        self._subscribers: List[Callable[[GameEvent], None]] = []

    def subscribe(self, handler: Callable[[GameEvent], None]):
        """Register a handler to receive all events."""
        self._subscribers.append(handler)

    def unsubscribe(self, handler: Callable[[GameEvent], None]):
        """Remove a handler."""
        self._subscribers.remove(handler)

    def emit(self, event: GameEvent):
        """Dispatch an event to all subscribers."""
        for handler in self._subscribers:
            handler(event)
