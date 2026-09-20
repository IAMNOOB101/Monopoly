"""Tests for bankruptcy mechanics and property transfers."""
import pytest
from monopoly.core.player import Player
from settings import StandardPlayerSettings, GameMechanics


class TestBankruptcy:
    """Test bankruptcy triggering and resolution."""

    def test_bankruptcy_on_unaffordable_rent(self, board, null_log):
        """Player goes bankrupt when they can't pay rent."""
        poor_player = Player("Poor", StandardPlayerSettings)
        poor_player.money = 10

        rich_player = Player("Rich", StandardPlayerSettings)
        rich_player.money = 5000

        poor_player.pay_money(100, rich_player, board, null_log)
        assert poor_player.is_bankrupt is True
        assert poor_player.money == 0

    def test_bankrupt_transfers_money_to_creditor(self, board, null_log):
        """Bankrupt player's remaining money goes to creditor."""
        poor_player = Player("Poor", StandardPlayerSettings)
        poor_player.money = 50

        rich_player = Player("Rich", StandardPlayerSettings)
        rich_player.money = 1000
        initial_rich_money = rich_player.money

        poor_player.pay_money(200, rich_player, board, null_log)
        assert poor_player.is_bankrupt is True
        # Rich player should have received the poor player's cash
        assert rich_player.money > initial_rich_money

    def test_bankrupt_transfers_property_to_player(self, board, null_log):
        """Bankrupt player's properties transfer to creditor player."""
        poor_player = Player("Poor", StandardPlayerSettings)
        poor_player.money = 10
        # Give poor player a property
        board.cells[1].owner = poor_player
        poor_player.owned.append(board.cells[1])

        rich_player = Player("Rich", StandardPlayerSettings)
        rich_player.money = 5000

        poor_player.pay_money(500, rich_player, board, null_log)
        assert poor_player.is_bankrupt is True
        assert len(poor_player.owned) == 0
        assert board.cells[1].owner == rich_player
        assert board.cells[1] in rich_player.owned

    def test_bankrupt_to_bank_resets_property(self, board, null_log):
        """Bankrupt to bank: properties become unowned and unmortgaged."""
        poor_player = Player("Poor", StandardPlayerSettings)
        poor_player.money = 10
        board.cells[1].owner = poor_player
        board.cells[1].is_mortgaged = True
        poor_player.owned.append(board.cells[1])

        poor_player.pay_money(500, "bank", board, null_log)
        assert poor_player.is_bankrupt is True
        assert board.cells[1].owner is None
        assert board.cells[1].is_mortgaged is False


class TestBankruptMortgageTax:
    """Test the official rule: 10% tax on inherited mortgaged properties."""

    def test_mortgage_tax_on_transfer(self, board, null_log):
        """Creditor pays 10% tax on inherited mortgaged property."""
        poor_player = Player("Poor", StandardPlayerSettings)
        poor_player.money = 10
        poor_starting_cash = poor_player.money
        # Give poor player Mediterranean ($60 base, mortgage value = $30)
        board.cells[1].owner = poor_player
        board.cells[1].is_mortgaged = True
        poor_player.owned.append(board.cells[1])

        rich_player = Player("Rich", StandardPlayerSettings)
        rich_player.money = 5000
        initial_rich = rich_player.money

        poor_player.pay_money(500, rich_player, board, null_log)

        # Rich player inherits the property
        assert board.cells[1] in rich_player.owned
        # Tax = mortgage_value * mortgage_fee = 60 * 0.5 * 0.1 = $3
        expected_tax = int(60 * GameMechanics.mortgage_value * GameMechanics.mortgage_fee)
        # Rich player received poor's cash but paid the tax
        # So rich = initial + poor_starting_cash - tax
        assert rich_player.money == initial_rich + poor_starting_cash - expected_tax


class TestRaiseMoney:
    """Test selling houses and mortgaging to raise money."""

    def test_sell_houses_to_pay_rent(self, board, null_log):
        """Player sells houses to pay rent when cash is insufficient."""
        player = Player("Seller", StandardPlayerSettings)
        player.money = 50

        # Give player Brown monopoly with houses
        for idx in [1, 3]:
            board.cells[idx].owner = player
            player.owned.append(board.cells[idx])
            board.cells[idx].has_houses = 2
        board.recalculate_monopoly_multipliers(board.cells[1])
        board.available_houses -= 4  # 2 houses on each

        initial_houses = board.available_houses
        player.raise_money(200, board, null_log)

        # Player should have sold some houses
        assert board.available_houses > initial_houses
        assert player.money >= 200 or (board.cells[1].has_houses == 0 and board.cells[3].has_houses == 0)

    def test_mortgage_property_to_pay(self, board, null_log):
        """Player mortgages property when no houses to sell."""
        player = Player("Mortgager", StandardPlayerSettings)
        player.money = 50

        board.cells[1].owner = player
        player.owned.append(board.cells[1])

        player.raise_money(80, board, null_log)
        assert board.cells[1].is_mortgaged is True
