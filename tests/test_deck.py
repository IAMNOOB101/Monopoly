"""Tests for deck draw/remove/add cycling correctness.
Validates the bug fixes for GOOJF card removal and reinsertion.
"""
import pytest
from monopoly.core.deck import Deck


class TestDeckDraw:
    """Test basic draw cycling."""

    def test_draw_returns_cards_in_order(self):
        """Cards are drawn in order."""
        deck = Deck(["A", "B", "C"])
        assert deck.draw() == "A"
        assert deck.draw() == "B"
        assert deck.draw() == "C"

    def test_draw_wraps_around(self):
        """Deck wraps around after all cards drawn."""
        deck = Deck(["A", "B", "C"])
        deck.draw()  # A
        deck.draw()  # B
        deck.draw()  # C
        assert deck.draw() == "A"  # Wraps around

    def test_draw_cycles_indefinitely(self):
        """Drawing continues cycling through the deck."""
        deck = Deck(["X", "Y"])
        results = [deck.draw() for _ in range(6)]
        assert results == ["X", "Y", "X", "Y", "X", "Y"]


class TestDeckRemove:
    """Test card removal (GOOJF mechanic)."""

    def test_remove_card_from_deck(self):
        """Removed card no longer appears in draw cycle."""
        deck = Deck(["A", "GOOJF", "B", "C"])
        deck.remove("GOOJF")
        results = [deck.draw() for _ in range(3)]
        assert "GOOJF" not in results
        assert results == ["A", "B", "C"]

    def test_remove_adjusts_pointer_before(self):
        """Removing a card before pointer adjusts pointer correctly."""
        deck = Deck(["A", "B", "C", "D"])
        deck.draw()  # A → pointer = 1
        deck.draw()  # B → pointer = 2
        deck.remove("A")  # Remove before pointer → pointer should adjust
        # Deck is now ["B", "C", "D"], pointer should point to "C"
        assert deck.draw() == "C"
        assert deck.draw() == "D"

    def test_remove_at_pointer(self):
        """Removing card at current pointer position."""
        deck = Deck(["A", "B", "C"])
        deck.draw()  # A → pointer = 1
        deck.remove("B")  # Remove at pointer
        # Deck is now ["A", "C"], pointer should be at "C" (index 1)
        assert deck.draw() == "C"

    def test_remove_wraps_pointer(self):
        """Removing when pointer is at end wraps it around."""
        deck = Deck(["A", "B"])
        deck.draw()  # A
        deck.draw()  # B → pointer = 0 (wrapped)
        deck.remove("A")  # Remove "A"
        # Deck is now ["B"], pointer should be 0
        assert deck.draw() == "B"


class TestDeckAdd:
    """Test card reinsertion (returning GOOJF)."""

    def test_add_card_back_to_deck(self):
        """Added card eventually appears in draws."""
        deck = Deck(["A", "B"])
        deck.remove("B")
        assert "B" not in deck.cards

        deck.add("B")
        assert "B" in deck.cards

    def test_added_card_not_immediate_next(self):
        """Added card should go to bottom, not be the next draw."""
        deck = Deck(["A", "B", "C"])
        deck.draw()  # A → pointer = 1
        deck.remove("C")  # Deck: ["A", "B"], pointer = 1

        # Add "C" back — it should go behind the pointer (bottom of undrawn pile)
        deck.add("C")

        # Next draw should be "B" (not "C")
        assert deck.draw() == "B"

    def test_add_when_pointer_is_zero(self):
        """BUG FIX: Adding card when pointer=0 should append to end, not insert at -1."""
        deck = Deck(["A", "B", "C"])
        # Draw all three to wrap pointer back to 0
        deck.draw()  # A
        deck.draw()  # B
        deck.draw()  # C → pointer wraps to 0

        deck.remove("C")
        # Deck: ["A", "B"], pointer = 0

        deck.add("C")
        # "C" should be at the end (since pointer=0, it goes to bottom)
        assert deck.cards[-1] == "C"

        # Drawing should give A, B, C in order
        assert deck.draw() == "A"
        assert deck.draw() == "B"
        assert deck.draw() == "C"

    def test_full_goojf_lifecycle(self):
        """Simulate full GOOJF lifecycle: draw → remove → use → add back."""
        deck = Deck(["Card1", "Get Out of Jail Free", "Card2", "Card3"])

        # Draw until we hit GOOJF
        deck.draw()  # Card1
        card = deck.draw()  # GOOJF
        assert card == "Get Out of Jail Free"

        # Remove GOOJF (player holds it)
        deck.remove("Get Out of Jail Free")
        assert len(deck.cards) == 3

        # Continue drawing — GOOJF should not appear
        results = [deck.draw() for _ in range(3)]
        assert "Get Out of Jail Free" not in results

        # Player uses GOOJF, returns it to deck
        deck.add("Get Out of Jail Free")
        assert len(deck.cards) == 4
        assert "Get Out of Jail Free" in deck.cards

        # Eventually should appear in future draws
        found = False
        for _ in range(10):
            if deck.draw() == "Get Out of Jail Free":
                found = True
                break
        assert found, "GOOJF card was never drawn after being returned"
