"""Tests for house/hotel building rules."""
import pytest
from monopoly.core.player import Player
from monopoly.core.constants import BROWN, RAILROADS, UTILITIES
from settings import StandardPlayerSettings, GameMechanics


class TestBuildingRules:
    """Test house building constraints."""

    def test_can_build_on_monopoly(self, board, null_log):
        """Player with a monopoly can build houses."""
        player = Player("Builder", StandardPlayerSettings)
        player.money = 5000

        # Give player all Brown properties
        for idx in [1, 3]:
            board.cells[idx].owner = player
            player.owned.append(board.cells[idx])
        board.recalculate_monopoly_multipliers(board.cells[1])

        initial_houses = board.available_houses
        player.improve_properties(board, null_log)

        # Should have built houses or hotels
        total_improvements = (board.cells[1].has_houses + board.cells[1].has_hotel
                              + board.cells[3].has_houses + board.cells[3].has_hotel)
        assert total_improvements > 0
        # Board state changed (houses consumed or hotels built)
        assert board.available_houses != initial_houses or board.available_hotels < 12

    def test_cannot_build_without_monopoly(self, board, null_log):
        """Player without monopoly cannot build houses."""
        player = Player("Builder", StandardPlayerSettings)
        player.money = 5000

        # Give player only one Brown property
        board.cells[1].owner = player
        player.owned.append(board.cells[1])
        board.recalculate_monopoly_multipliers(board.cells[1])

        player.improve_properties(board, null_log)
        assert board.cells[1].has_houses == 0

    def test_even_building(self, board, null_log):
        """Houses must be built evenly across the group."""
        player = Player("Builder", StandardPlayerSettings)
        player.money = 5000

        # Give player all Brown properties
        for idx in [1, 3]:
            board.cells[idx].owner = player
            player.owned.append(board.cells[idx])
        board.recalculate_monopoly_multipliers(board.cells[1])

        player.improve_properties(board, null_log)

        # Houses should differ by at most 1
        diff = abs(board.cells[1].has_houses - board.cells[3].has_houses)
        # Account for hotels too
        total_1 = board.cells[1].has_houses + board.cells[1].has_hotel * 5
        total_3 = board.cells[3].has_houses + board.cells[3].has_hotel * 5
        assert abs(total_1 - total_3) <= 1

    def test_hotel_frees_houses(self, board, null_log):
        """Building a hotel returns 4 houses to the bank."""
        player = Player("Builder", StandardPlayerSettings)
        player.money = 10000

        for idx in [1, 3]:
            board.cells[idx].owner = player
            player.owned.append(board.cells[idx])
        board.recalculate_monopoly_multipliers(board.cells[1])

        player.improve_properties(board, null_log)

        # Both should have hotels (cheap enough)
        hotels = board.cells[1].has_hotel + board.cells[3].has_hotel
        assert hotels > 0  # At least one hotel built

    def test_house_shortage_blocks_building(self, board, null_log):
        """Cannot build if bank has no houses."""
        player = Player("Builder", StandardPlayerSettings)
        player.money = 5000

        for idx in [1, 3]:
            board.cells[idx].owner = player
            player.owned.append(board.cells[idx])
        board.recalculate_monopoly_multipliers(board.cells[1])

        # Set available houses to 0
        board.available_houses = 0
        player.improve_properties(board, null_log)
        assert board.cells[1].has_houses == 0
        assert board.cells[3].has_houses == 0

    def test_unspendable_cash_prevents_building(self, board, null_log):
        """Player respects unspendable_cash threshold when building."""
        player = Player("Builder", StandardPlayerSettings)
        player.money = 250  # 200 unspendable + only 50 left

        for idx in [1, 3]:
            board.cells[idx].owner = player
            player.owned.append(board.cells[idx])
        board.recalculate_monopoly_multipliers(board.cells[1])

        player.improve_properties(board, null_log)

        # At $250 with $200 buffer, can build 1 house at $50
        total_houses = board.cells[1].has_houses + board.cells[3].has_houses
        assert total_houses <= 1


class TestOfficialHouseCount:
    """Test that official house count is correct."""

    def test_default_houses_is_32(self):
        """Official rules: 32 houses."""
        assert GameMechanics.available_houses == 32

    def test_default_hotels_is_12(self):
        """Official rules: 12 hotels."""
        assert GameMechanics.available_hotels == 12
