"""Tests for jail mechanics."""
import pytest
from monopoly.core.player import Player
from monopoly.core.move_result import MoveResult
from settings import StandardPlayerSettings


class TestGoingToJail:
    """Test entering jail."""

    def test_go_to_jail_sets_position(self, standard_player, null_log):
        """Going to jail sets position to 10."""
        standard_player.position = 30  # Go To Jail cell
        standard_player.handle_going_to_jail("test", null_log)
        assert standard_player.position == 10
        assert standard_player.in_jail is True

    def test_go_to_jail_resets_doubles(self, standard_player, null_log):
        """Going to jail resets doubles counter."""
        standard_player.had_doubles = 2
        standard_player.handle_going_to_jail("test", null_log)
        assert standard_player.had_doubles == 0

    def test_go_to_jail_resets_days(self, standard_player, null_log):
        """Going to jail resets days_in_jail."""
        standard_player.days_in_jail = 1
        standard_player.handle_going_to_jail("test", null_log)
        assert standard_player.days_in_jail == 0


class TestJailExit:
    """Test various ways to exit jail."""

    def test_exit_on_doubles(self, standard_player, board, null_log):
        """Player exits jail when rolling doubles."""
        standard_player.in_jail = True
        standard_player.days_in_jail = 0
        result = standard_player.is_player_stay_in_jail(True, board, null_log)
        assert result is False
        assert standard_player.in_jail is False

    def test_stay_without_doubles_day1(self, standard_player, board, null_log):
        """Player stays in jail without doubles on day 1."""
        standard_player.in_jail = True
        standard_player.days_in_jail = 0
        result = standard_player.is_player_stay_in_jail(False, board, null_log)
        assert result is True
        assert standard_player.in_jail is True
        assert standard_player.days_in_jail == 1

    def test_forced_exit_day3(self, standard_player, board, null_log):
        """Player forced out on 3rd day, pays fine."""
        standard_player.in_jail = True
        standard_player.days_in_jail = 2
        initial_money = standard_player.money
        result = standard_player.is_player_stay_in_jail(False, board, null_log)
        assert result is False
        assert standard_player.in_jail is False
        assert standard_player.money < initial_money  # Paid the fine

    def test_exit_with_goojf_chance(self, standard_player, board, null_log):
        """Player uses Chance GOOJF card to exit."""
        standard_player.in_jail = True
        standard_player.get_out_of_jail_chance = True
        # Remove the card from the deck first (simulating player holding it)
        board.chance.remove("Get Out of Jail Free")

        result = standard_player.is_player_stay_in_jail(False, board, null_log)
        assert result is False
        assert standard_player.in_jail is False
        assert standard_player.get_out_of_jail_chance is False
        # Card should be back in the deck
        assert "Get Out of Jail Free" in board.chance.cards

    def test_exit_with_goojf_comm_chest(self, standard_player, board, null_log):
        """Player uses Community Chest GOOJF card to exit."""
        standard_player.in_jail = True
        standard_player.get_out_of_jail_comm_chest = True
        board.chest.remove("Get Out of Jail Free")

        result = standard_player.is_player_stay_in_jail(False, board, null_log)
        assert result is False
        assert standard_player.in_jail is False
        assert standard_player.get_out_of_jail_comm_chest is False
        assert "Get Out of Jail Free" in board.chest.cards
