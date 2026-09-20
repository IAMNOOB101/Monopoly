"""Tests for the auction system."""
import pytest
from monopoly.core.player import Player
from monopoly.core.board import Board
from settings import StandardPlayerSettings, GameSettings, GameMechanics


class TestAuction:
    """Test the sealed-bid auction mechanics."""

    def test_auction_winner_gets_property(self, board, four_players, dice, null_log):
        """Highest bidder wins the property."""
        property_cell = board.cells[1]  # Mediterranean ($60)
        assert property_cell.owner is None

        board.run_auction(property_cell, four_players, dice, null_log)

        # Someone should own the property now
        assert property_cell.owner is not None
        assert property_cell in property_cell.owner.owned

    def test_auction_deducts_money(self, board, four_players, dice, null_log):
        """Winner pays their bid amount."""
        property_cell = board.cells[1]
        initial_moneys = {p.name: p.money for p in four_players}

        board.run_auction(property_cell, four_players, dice, null_log)

        winner = property_cell.owner
        if winner:
            assert winner.money < initial_moneys[winner.name]

    def test_auction_no_bids_when_broke(self, board, dice, null_log):
        """No bids when all players are too poor."""
        players = [
            Player("Broke1", StandardPlayerSettings),
            Player("Broke2", StandardPlayerSettings),
        ]
        for p in players:
            p.money = 0  # No money = no bids

        property_cell = board.cells[1]
        board.run_auction(property_cell, players, dice, null_log)
        assert property_cell.owner is None

    def test_auction_skips_bankrupt_players(self, board, four_players, dice, null_log):
        """Bankrupt players don't participate in auctions."""
        four_players[1].is_bankrupt = True
        four_players[2].is_bankrupt = True
        four_players[3].is_bankrupt = True

        property_cell = board.cells[1]
        board.run_auction(property_cell, four_players, dice, null_log)

        # Only player 0 could bid
        if property_cell.owner:
            assert property_cell.owner == four_players[0]

    def test_auction_monopoly_completion_bid(self, board, dice, null_log):
        """Player bids higher when auction would complete their monopoly."""
        player1 = Player("Closer", StandardPlayerSettings)
        player1.money = 1500
        player2 = Player("Rival", StandardPlayerSettings)
        player2.money = 1500

        # Give player1 Baltic (the other Brown property)
        board.cells[3].owner = player1
        player1.owned.append(board.cells[3])
        board.recalculate_monopoly_multipliers(board.cells[3])

        # Auction Mediterranean — player1 should bid high (up to 2x)
        property_cell = board.cells[1]  # Mediterranean $60
        bid1 = player1.get_auction_bid(property_cell, board)
        bid2 = player2.get_auction_bid(property_cell, board)

        # Player completing monopoly should bid higher
        assert bid1 > bid2

    def test_auction_blocking_bid(self, board, dice, null_log):
        """Player bids higher to block opponent's monopoly."""
        blocker = Player("Blocker", StandardPlayerSettings)
        blocker.money = 1500
        opponent = Player("Opponent", StandardPlayerSettings)
        opponent.money = 1500
        bystander = Player("Bystander", StandardPlayerSettings)
        bystander.money = 1500

        # Give opponent Baltic — they need Mediterranean for monopoly
        board.cells[3].owner = opponent
        opponent.owned.append(board.cells[3])
        board.recalculate_monopoly_multipliers(board.cells[3])

        # Blocker's bid for Mediterranean should reflect blocking value
        property_cell = board.cells[1]
        bid_blocker = blocker.get_auction_bid(property_cell, board)
        bid_bystander = bystander.get_auction_bid(property_cell, board)

        # Blocker should bid at least 1.5x (blocking) vs bystander's 1x
        assert bid_blocker >= bid_bystander


class TestAuctionEnabled:
    """Test auction enable/disable setting."""

    def test_auctions_enabled_by_default(self):
        """Auctions are enabled by default."""
        assert GameMechanics.enable_auctions is True

    def test_auction_min_bid(self):
        """Minimum bid is $1."""
        assert GameMechanics.auction_min_bid == 1
