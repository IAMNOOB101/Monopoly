"""Tests for rent calculation across all property types."""
import pytest
from monopoly.core.cell import Property
from monopoly.core.constants import BROWN, LIGHTBLUE, RAILROADS, UTILITIES


class TestBaseRent:
    """Test base rent (no houses, no monopoly)."""

    def test_brown_base_rent(self, board):
        """Mediterranean Avenue base rent is $2."""
        cell = board.cells[1]  # Mediterranean
        assert cell.rent_base == 2

    def test_lightblue_base_rent(self, board):
        """Oriental Avenue base rent is $6."""
        cell = board.cells[6]  # Oriental
        assert cell.rent_base == 6

    def test_boardwalk_base_rent(self, board):
        """Boardwalk base rent is $50."""
        cell = board.cells[39]  # Boardwalk
        assert cell.rent_base == 50


class TestMonopolyRent:
    """Test rent doubling with monopoly (no houses)."""

    def test_brown_monopoly_doubles_rent(self, board, standard_player, dice):
        """Owning both Brown properties doubles rent."""
        for idx in [1, 3]:
            board.cells[idx].owner = standard_player
            standard_player.owned.append(board.cells[idx])
        board.recalculate_monopoly_multipliers(board.cells[1])

        rent = board.cells[1].calculate_rent(dice)
        assert rent == 4  # 2 * 2 = 4

    def test_no_monopoly_single_rent(self, board, standard_player, dice):
        """Owning one of a group gives 1x rent."""
        board.cells[1].owner = standard_player
        standard_player.owned.append(board.cells[1])
        board.recalculate_monopoly_multipliers(board.cells[1])

        rent = board.cells[1].calculate_rent(dice)
        assert rent == 2  # 2 * 1 = 2


class TestHouseRent:
    """Test rent with houses and hotels."""

    def test_one_house_rent(self, board, dice):
        """Mediterranean with 1 house = $10."""
        cell = board.cells[1]
        cell.has_houses = 1
        rent = cell.calculate_rent(dice)
        assert rent == 10

    def test_four_houses_rent(self, board, dice):
        """Mediterranean with 4 houses = $160."""
        cell = board.cells[1]
        cell.has_houses = 4
        rent = cell.calculate_rent(dice)
        assert rent == 160

    def test_hotel_rent(self, board, dice):
        """Mediterranean with hotel = $250."""
        cell = board.cells[1]
        cell.has_hotel = 1
        rent = cell.calculate_rent(dice)
        assert rent == 250

    def test_boardwalk_hotel(self, board, dice):
        """Boardwalk with hotel = $2000."""
        cell = board.cells[39]
        cell.has_hotel = 1
        rent = cell.calculate_rent(dice)
        assert rent == 2000


class TestRailroadRent:
    """Test railroad rent scaling with ownership count."""

    def test_one_railroad(self, board, standard_player, dice):
        """One railroad = $25."""
        board.cells[5].owner = standard_player
        standard_player.owned.append(board.cells[5])
        board.recalculate_monopoly_multipliers(board.cells[5])
        rent = board.cells[5].calculate_rent(dice)
        assert rent == 25

    def test_two_railroads(self, board, standard_player, dice):
        """Two railroads = $50."""
        for idx in [5, 15]:
            board.cells[idx].owner = standard_player
            standard_player.owned.append(board.cells[idx])
        board.recalculate_monopoly_multipliers(board.cells[5])
        rent = board.cells[5].calculate_rent(dice)
        assert rent == 50

    def test_four_railroads(self, board, standard_player, dice):
        """Four railroads = $200."""
        for idx in [5, 15, 25, 35]:
            board.cells[idx].owner = standard_player
            standard_player.owned.append(board.cells[idx])
        board.recalculate_monopoly_multipliers(board.cells[5])
        rent = board.cells[5].calculate_rent(dice)
        assert rent == 200


class TestUtilityRent:
    """Test utility rent based on dice roll and ownership."""

    def test_one_utility_multiplier(self, board, standard_player):
        """One utility: multiplier is 4."""
        board.cells[12].owner = standard_player
        standard_player.owned.append(board.cells[12])
        board.recalculate_monopoly_multipliers(board.cells[12])
        assert board.cells[12].monopoly_multiplier == 4

    def test_two_utilities_multiplier(self, board, standard_player):
        """Two utilities: multiplier is 10."""
        for idx in [12, 28]:
            board.cells[idx].owner = standard_player
            standard_player.owned.append(board.cells[idx])
        board.recalculate_monopoly_multipliers(board.cells[12])
        assert board.cells[12].monopoly_multiplier == 10
