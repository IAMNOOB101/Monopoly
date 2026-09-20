"""Tests for Chance and Community Chest card effects.
Verifies the bug fixes for 'You inherit $100' and 'Birthday $10'.
"""
import pytest
from monopoly.core.player import Player
from monopoly.core.move_result import MoveResult
from settings import StandardPlayerSettings


class TestChanceCards:
    """Test Chance card effects."""

    def test_advance_to_boardwalk(self, standard_player, board, four_players, null_log):
        """Chance: Advance to Boardwalk sends to position 39."""
        # Force the card
        board.chance.cards = ["Advance to Boardwalk"]
        board.chance.pointer = 0

        standard_player.position = 7  # Chance cell
        standard_player.handle_chance(board, four_players, null_log)
        assert standard_player.position == 39

    def test_advance_to_go(self, standard_player, board, four_players, null_log):
        """Chance: Advance to Go moves to 0 and gives salary."""
        board.chance.cards = ["Advance to Go (Collect $200)"]
        board.chance.pointer = 0
        initial_money = standard_player.money

        standard_player.position = 7
        standard_player.handle_chance(board, four_players, null_log)
        assert standard_player.position == 0
        assert standard_player.money == initial_money + 200  # salary

    def test_go_to_jail_card(self, standard_player, board, four_players, null_log):
        """Chance: Go to Jail card sends to jail."""
        board.chance.cards = [
            "Go to Jail. Go directly to Jail, do not pass Go, do not collect $200"
        ]
        board.chance.pointer = 0

        result = standard_player.handle_chance(board, four_players, null_log)
        assert result == MoveResult.END_MOVE
        assert standard_player.position == 10
        assert standard_player.in_jail is True

    def test_bank_pays_50(self, standard_player, board, four_players, null_log):
        """Chance: Bank pays you $50."""
        board.chance.cards = ["Bank pays you dividend of $50"]
        board.chance.pointer = 0
        initial_money = standard_player.money

        standard_player.handle_chance(board, four_players, null_log)
        assert standard_player.money == initial_money + 50

    def test_speeding_fine(self, standard_player, board, four_players, null_log):
        """Chance: Speeding fine $15."""
        board.chance.cards = ["Speeding fine $15"]
        board.chance.pointer = 0
        initial_money = standard_player.money

        standard_player.handle_chance(board, four_players, null_log)
        assert standard_player.money == initial_money - 15

    def test_building_loan_matures(self, standard_player, board, four_players, null_log):
        """Chance: Building loan matures, collect $150."""
        board.chance.cards = ["Your building loan matures. Collect $150"]
        board.chance.pointer = 0
        initial_money = standard_player.money

        standard_player.handle_chance(board, four_players, null_log)
        assert standard_player.money == initial_money + 150

    def test_goojf_card_chance(self, standard_player, board, four_players, null_log):
        """Chance: Get Out of Jail Free card is retained by player."""
        board.chance.cards = ["Get Out of Jail Free", "Speeding fine $15"]
        board.chance.pointer = 0

        standard_player.handle_chance(board, four_players, null_log)
        assert standard_player.get_out_of_jail_chance is True
        assert "Get Out of Jail Free" not in board.chance.cards


class TestCommunityChestCards:
    """Test Community Chest card effects."""

    def test_inherit_100_bug_fix(self, standard_player, board, four_players, null_log):
        """BUG FIX: 'You inherit $100' should give $100 (was broken by string concatenation)."""
        board.chest.cards = ["You inherit $100"]
        board.chest.pointer = 0
        initial_money = standard_player.money

        standard_player.handle_community_chest(board, four_players, null_log)
        assert standard_player.money == initial_money + 100

    def test_birthday_card_bug_fix(self, four_players, board, null_log):
        """BUG FIX: Birthday card should charge $10 per player (was $50)."""
        board.chest.cards = ["It is your birthday. Collect $10 from every player"]
        board.chest.pointer = 0

        birthday_player = four_players[0]
        initial_money_birthday = birthday_player.money
        initial_money_others = [p.money for p in four_players[1:]]

        birthday_player.handle_community_chest(board, four_players, null_log)

        # Birthday player should receive $10 from each of 3 other players = $30
        assert birthday_player.money == initial_money_birthday + 30
        # Each other player should lose $10
        for i, player in enumerate(four_players[1:]):
            assert player.money == initial_money_others[i] - 10

    def test_bank_error_200(self, standard_player, board, four_players, null_log):
        """Community Chest: Bank error, collect $200."""
        board.chest.cards = ["Bank error in your favor. Collect $200"]
        board.chest.pointer = 0
        initial_money = standard_player.money

        standard_player.handle_community_chest(board, four_players, null_log)
        assert standard_player.money == initial_money + 200

    def test_doctor_fee(self, standard_player, board, four_players, null_log):
        """Community Chest: Doctor's fee, pay $50."""
        board.chest.cards = ["Doctor's fee. Pay $50"]
        board.chest.pointer = 0
        initial_money = standard_player.money

        standard_player.handle_community_chest(board, four_players, null_log)
        assert standard_player.money == initial_money - 50

    def test_advance_to_go_cc(self, standard_player, board, four_players, null_log):
        """Community Chest: Advance to Go."""
        board.chest.cards = ["Advance to Go (Collect $200)"]
        board.chest.pointer = 0
        initial_money = standard_player.money

        standard_player.handle_community_chest(board, four_players, null_log)
        assert standard_player.position == 0
        assert standard_player.money == initial_money + 200

    def test_goojf_card_cc(self, standard_player, board, four_players, null_log):
        """Community Chest: Get Out of Jail Free card."""
        board.chest.cards = ["Get Out of Jail Free", "Doctor's fee. Pay $50"]
        board.chest.pointer = 0

        standard_player.handle_community_chest(board, four_players, null_log)
        assert standard_player.get_out_of_jail_comm_chest is True
        assert "Get Out of Jail Free" not in board.chest.cards
