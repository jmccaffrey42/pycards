

class Card:
    CARD_SUITS = [
        'h', 's', 'c', 'd'
    ]

    # SUIT_TO_INT = dict(zip(CARD_SUITS, range(4)))

    CARD_FACES = [
        'A', '2', '3', '4', '5', '6',
        '7', '8', '9', '10', 'J', 'Q', 'K'
    ]

    # FACE_TO_INT = dict(zip(CARD_FACES, range(13)))

    def __init__(self, key):
        (face, suit) = (key[:-1], key[-1:])

        if face not in Card.CARD_FACES or suit not in Card.CARD_SUITS:
            raise(ValueError("Invalid suit or face in {}".format(key)))

        self.face = face
        self.suit = suit

    def __str__(self):
        return self.face + self.suit
