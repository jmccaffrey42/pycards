import random
from pycards.card import Card


class Deck:
    def __init__(self, num_decks=1):
        self.cards = [Card(f + s) for f in Card.CARD_FACES for s in Card.CARD_SUITS] * num_decks
        random.shuffle(self.cards)

    def deal(self, n):
        if len(self.cards) < n:
            raise(IndexError("there are not enough cards to deal {}".format(n)))
        
        hand = self.cards[0:n]
        del self.cards[0:n]
        return hand
