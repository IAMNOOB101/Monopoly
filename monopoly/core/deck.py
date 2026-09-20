""" Deck class for Community Chest and Chance cards.
Uses a circular pointer to cycle through a shuffled list of cards.
Supports removing cards (GOOJF) and returning them to the deck.
"""


class Deck:
    """ Parent for Community Chest and Chance cards
    """

    def __init__(self, cards):
        # List of cards
        self.cards = cards
        # Pointer to the next card to draw
        self.pointer = 0

    def draw(self):
        """ Draw one card from the deck and put it underneath.
        Actually, we don't manipulate cards, just shuffle them once
        and then move the pointer through the deck.
        """
        drawn_card = self.cards[self.pointer]
        self.pointer += 1
        if self.pointer >= len(self.cards):
            self.pointer = 0
        return drawn_card

    def remove(self, card_to_remove):
        """ Remove a card (used for GOOJF card).
        Adjusts the pointer to account for the shifted indices.
        """
        index = self.cards.index(card_to_remove)
        self.cards.pop(index)

        # If the removed card was before the pointer, shift pointer back
        # to keep it pointing at the same logical card
        if index < self.pointer:
            self.pointer -= 1

        # Safety: wrap pointer if it's past the end
        if len(self.cards) > 0 and self.pointer >= len(self.cards):
            self.pointer = 0

    def add(self, card_to_add):
        """ Add card back to the deck (to put the removed GOOJF card back
        once it's been used). The card is inserted just before the current
        pointer so it goes to the "bottom" of the undrawn pile and won't
        be drawn again until the deck fully cycles.
        """
        if self.pointer == 0:
            # Pointer at front: append to end (bottom of deck)
            self.cards.append(card_to_add)
        else:
            # Insert just before the pointer; then advance pointer
            # so the returned card sits behind us in the cycle
            self.cards.insert(self.pointer, card_to_add)
            self.pointer += 1
