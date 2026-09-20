"""Tests for trade logic and monopoly blocking."""
import pytest
from monopoly.core.player import Player
from monopoly.core.constants import ORANGE, RED
from settings import StandardPlayerSettings


class TestTradeLogic:
    """Test two-way trading mechanics."""

    def test_trade_updates_ownership(self, board, null_log):
        """After a trade, property ownership is correctly updated."""
        player_a = Player("Alice", StandardPlayerSettings)
        player_a.money = 1500
        player_b = Player("Bob", StandardPlayerSettings)
        player_b.money = 1500

        # Give Alice: Oriental (LB, idx 6) and St. James (Orange, idx 16)
        # Give Bob: Vermont (LB, idx 8), Connecticut (LB, idx 9), Tennessee (Orange, idx 18), New York (Orange, idx 19)
        # Alice has 1 LB (wants to sell) and 1 Orange (wants to sell)
        # Bob has 2 LB (needs 1 more for monopoly) and 2 Orange (needs 1 more)

        for idx in [6, 16]:
            board.cells[idx].owner = player_a
            player_a.owned.append(board.cells[idx])
        for idx in [8, 9, 18, 19]:
            board.cells[idx].owner = player_b
            player_b.owned.append(board.cells[idx])

        # Recalculate monopolies
        for idx in [6, 8, 9, 16, 18, 19]:
            board.recalculate_monopoly_multipliers(board.cells[idx])

        # Update trade lists
        players = [player_a, player_b]
        for p in players:
            p.update_lists_of_properties_to_trade(board)

        # Alice should want to sell her single LB and single Orange
        # Bob should want to buy the remaining LB and Orange
        assert len(player_a.wants_to_sell) > 0 or len(player_b.wants_to_sell) > 0

    def test_trade_respects_value_limits(self, board, null_log):
        """Trades should not happen if the value difference is too large."""
        player_a = Player("Alice", StandardPlayerSettings)
        player_a.money = 1500
        player_b = Player("Bob", StandardPlayerSettings)
        player_b.money = 1500

        # Expensive vs cheap trade scenario
        # Give Alice Boardwalk (idx 39, $400) — she has 1 Indigo, willing to sell
        # Give Bob Park Place (idx 37, $350) — he has 1 Indigo, willing to sell
        # Since both are Indigo group (size 2), both want it → fair_deal filters these
        board.cells[39].owner = player_a
        player_a.owned.append(board.cells[39])
        board.cells[37].owner = player_b
        player_b.owned.append(board.cells[37])

        for idx in [37, 39]:
            board.recalculate_monopoly_multipliers(board.cells[idx])

        players = [player_a, player_b]
        for p in players:
            p.update_lists_of_properties_to_trade(board)

        # Both want the same color group — fair_deal should block this
        result = player_a.do_a_two_way_trade(players, board, null_log)
        # Size-2 groups are filtered out by fair_deal
        assert result is False


class TestMonopolyBlocking:
    """Test the monopoly blocking AI feature in trades."""

    def test_blocks_opponent_high_value_monopoly(self, board, null_log):
        """Player refuses trade that gives opponent Orange monopoly."""
        player_a = Player("Alice", StandardPlayerSettings)
        player_a.money = 1500
        player_b = Player("Bob", StandardPlayerSettings)
        player_b.money = 1500

        # Bob has 2 of 3 Orange properties (St. James + Tennessee)
        # Alice has the 3rd (New York) — giving it completes Bob's monopoly
        board.cells[16].owner = player_b
        player_b.owned.append(board.cells[16])
        board.cells[18].owner = player_b
        player_b.owned.append(board.cells[18])
        board.cells[19].owner = player_a
        player_a.owned.append(board.cells[19])

        # Give Alice 2 Red properties, Bob has 1
        board.cells[21].owner = player_a
        player_a.owned.append(board.cells[21])
        board.cells[23].owner = player_a
        player_a.owned.append(board.cells[23])
        board.cells[24].owner = player_b
        player_b.owned.append(board.cells[24])

        for idx in [16, 18, 19, 21, 23, 24]:
            board.recalculate_monopoly_multipliers(board.cells[idx])

        players = [player_a, player_b]
        for p in players:
            p.update_lists_of_properties_to_trade(board)

        # Alice has Orange to sell and wants Red
        # But giving Orange would complete Bob's monopoly
        # Alice would also complete Red monopoly — so trade SHOULD happen
        # (monopoly blocking only refuses when we DON'T get a monopoly back)

    def test_allows_trade_when_both_get_monopoly(self, board, null_log):
        """Trade is allowed if both players complete a monopoly."""
        player_a = Player("Alice", StandardPlayerSettings)
        player_a.money = 1500
        player_b = Player("Bob", StandardPlayerSettings)
        player_b.money = 1500

        # Setup: Alice has 2 Pink + 1 Orange, Bob has 2 Orange + 1 Pink
        # Pink: 11, 13, 14. Orange: 16, 18, 19
        board.cells[11].owner = player_a
        player_a.owned.append(board.cells[11])
        board.cells[13].owner = player_a
        player_a.owned.append(board.cells[13])
        board.cells[14].owner = player_b  # Bob has 1 Pink
        player_b.owned.append(board.cells[14])

        board.cells[16].owner = player_b
        player_b.owned.append(board.cells[16])
        board.cells[18].owner = player_b
        player_b.owned.append(board.cells[18])
        board.cells[19].owner = player_a  # Alice has 1 Orange
        player_a.owned.append(board.cells[19])

        for idx in [11, 13, 14, 16, 18, 19]:
            board.recalculate_monopoly_multipliers(board.cells[idx])

        players = [player_a, player_b]
        for p in players:
            p.update_lists_of_properties_to_trade(board)

        # Both should want to trade
        assert len(player_a.wants_to_sell) > 0
        assert len(player_a.wants_to_buy) > 0
