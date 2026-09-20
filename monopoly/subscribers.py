""" Event subscribers for data collection and structured logging.
These subscribers listen to GameEvents emitted by the engine
and collect data for analytics and visualization.
"""
from collections import defaultdict
from typing import List, Dict, Tuple

from monopoly.core.events import (
    GameEvent, PlayerMoved, TurnSnapshot, PlayerBankrupt,
    AuctionCompleted, TradeCompleted, GameStarted, GameEnded,
    PropertyBought, RentPaid, HouseBuilt, HotelBuilt
)


class DataSubscriber:
    """Collects structured game data for post-simulation analytics.

    Tracks:
    - Per-turn net worths for trajectory analysis
    - Landing positions for board heatmap
    - Bankruptcy events for survival analysis
    - Auction results
    - Trade activity
    """

    def __init__(self):
        # (game_number, turn, player_name) -> net_worth
        self.net_worths: List[Tuple[int, int, str, int]] = []
        # (game_number, turn, player_name, position)
        self.landings: List[Tuple[int, int, str, int]] = []
        # (game_number, player_name, turn)
        self.bankruptcies: List[Tuple[int, str, int]] = []
        # Auction outcomes
        self.auctions: List[dict] = []
        # Trade outcomes
        self.trades: List[dict] = []
        # Game outcomes
        self.game_results: List[dict] = []

    def handle(self, event: GameEvent):
        """Route events to appropriate collection methods."""

        if isinstance(event, TurnSnapshot):
            for player_name, nw in event.player_net_worths.items():
                self.net_worths.append(
                    (event.game_number, event.turn, player_name, nw))
            for player_name, pos in event.player_positions.items():
                self.landings.append(
                    (event.game_number, event.turn, player_name, pos))

        elif isinstance(event, PlayerMoved):
            self.landings.append(
                (event.game_number, event.turn, event.player_name, event.to_position))

        elif isinstance(event, PlayerBankrupt):
            self.bankruptcies.append(
                (event.game_number, event.player_name, event.turn))

        elif isinstance(event, AuctionCompleted):
            self.auctions.append({
                "game": event.game_number,
                "turn": event.turn,
                "property": event.property_name,
                "winner": event.winner,
                "price": event.winning_bid,
                "bidders": event.num_bidders,
            })

        elif isinstance(event, TradeCompleted):
            self.trades.append({
                "game": event.game_number,
                "turn": event.turn,
                "player_a": event.player_a,
                "player_b": event.player_b,
                "a_gives": event.a_gives,
                "b_gives": event.b_gives,
                "cash": event.cash_compensation,
            })

        elif isinstance(event, GameEnded):
            self.game_results.append({
                "game": event.game_number,
                "turn": event.turn,
                "reason": event.reason,
                "survivors": event.survivors,
            })

    def get_landing_counts(self) -> Dict[int, int]:
        """Return {position: count} for board heatmap."""
        counts: Dict[int, int] = defaultdict(int)
        for _, _, _, pos in self.landings:
            counts[pos] += 1
        return dict(counts)
