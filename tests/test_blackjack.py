import unittest

from pycards.blackjack import BjGameState, BjPlayerUpdate, BjPlayerActions, BjPhases, BjGameError, BjHandOutcomes, BjHand
from pycards.card import Card


class TestBjGameState(unittest.TestCase):
    def test_invalid_action(self):
        gs = BjGameState()
        with self.assertRaises(BjGameError):
            gs.update(BjPlayerUpdate(-1))

    def test_deck(self):
        gs = BjGameState()

        aces_in_deck = list(filter(lambda c: c.face == 'A', gs.deck.cards))
        self.assertEqual(6 * 52, len(gs.deck.cards))
        self.assertEqual(6 * 4, len(aces_in_deck))

    def test_join(self):
        gs = BjGameState()

        gs = gs.update(BjPlayerUpdate(BjPlayerActions.JOIN, bet_amt=1000))
        self.assertEqual(1, len(gs.players))
        self.assertEqual(gs.players[0].id, gs.current_turn_player_id)
        self.assertEqual(1000, gs.players[0].total_credit)

        gs = gs.update(BjPlayerUpdate(BjPlayerActions.JOIN, bet_amt=2000))
        self.assertEqual(2, len(gs.players))
        self.assertEqual(gs.players[0].id, gs.current_turn_player_id)
        self.assertEqual(1000, gs.players[0].total_credit)
        self.assertEqual(2000, gs.players[1].total_credit)

    def test_failed_join(self):
        gs = BjGameState()
        gs.current_phase = BjPhases.PLAY

        with self.assertRaises(BjGameError):
            gs.update(BjPlayerUpdate(BjPlayerActions.JOIN, bet_amt=1000))

    def test_single_bet(self):
        gs = BjGameState()
        self.assertEqual(BjPhases.END, gs.current_phase)

        gs = gs.update(BjPlayerUpdate(BjPlayerActions.JOIN, bet_amt=1000))

        player = gs.players[0]

        gs = gs.update(BjPlayerUpdate(BjPlayerActions.BET, player_id=player.id, hand_idx=0, bet_amt=100))

        self.assertEqual(900, gs.players[0].total_credit)
        self.assertEqual(100, gs.players[0].hands[0].bet_amt)

    def test_out_of_turn(self):
        gs = BjGameState()
        gs = gs.update(BjPlayerUpdate(BjPlayerActions.JOIN, bet_amt=1000))
        gs = gs.update(BjPlayerUpdate(BjPlayerActions.JOIN, bet_amt=1000))

        p2 = gs.players[1]

        with self.assertRaises(BjGameError):
            gs.update(BjPlayerUpdate(BjPlayerActions.BET, player_id=p2.id, hand_idx=0, bet_amt=100))

    def test_bet_turns(self):
        gs = BjGameState()
        gs = gs.update(BjPlayerUpdate(BjPlayerActions.JOIN, bet_amt=1000))
        gs = gs.update(BjPlayerUpdate(BjPlayerActions.JOIN, bet_amt=1000))

        p1 = gs.players[0]
        p2 = gs.players[1]

        gs = gs.update(BjPlayerUpdate(BjPlayerActions.BET, player_id=p1.id, hand_idx=0, bet_amt=100))
        gs = gs.update(BjPlayerUpdate(BjPlayerActions.BET, player_id=p2.id, hand_idx=0, bet_amt=50))

        self.assertEqual(900, gs.players[0].total_credit)
        self.assertEqual(100, gs.players[0].hands[0].bet_amt)
        self.assertEqual(950, gs.players[1].total_credit)
        self.assertEqual(50, gs.players[1].hands[0].bet_amt)

    def test_phase_bet_play(self):
        gs = BjGameState()

        # This keeps the dealer from getting an Ace first and going to an insurance round
        gs.deck.cards[4].face = 'J'

        gs = gs.update(BjPlayerUpdate(BjPlayerActions.JOIN, bet_amt=1000))
        gs = gs.update(BjPlayerUpdate(BjPlayerActions.JOIN, bet_amt=1000))

        p1 = gs.players[0]
        p2 = gs.players[1]

        self.assertEqual(BjPhases.END, gs.current_phase)
        gs = gs.update(BjPlayerUpdate(BjPlayerActions.BET, player_id=p1.id, hand_idx=0, bet_amt=100))
        self.assertEqual(BjPhases.BET, gs.current_phase)
        gs = gs.update(BjPlayerUpdate(BjPlayerActions.BET, player_id=p2.id, hand_idx=0, bet_amt=50))
        self.assertEqual(BjPhases.PLAY, gs.current_phase)

    def test_deal(self):
        gs = TestBjGameState._setup_game([100, 100, 100, 100])

        self.assertEqual(2, len(gs.players[0].hands[0].cards))
        self.assertEqual(2, len(gs.players[1].hands[0].cards))
        self.assertEqual(2, len(gs.dealer.hands[0].cards))

    def test_stand(self):
        gs = TestBjGameState._setup_game([100])

        gs = gs.update(BjPlayerUpdate(BjPlayerActions.STAND, gs.players[0].id, 0))
        self.assertEqual(BjPhases.END, gs.current_phase)
        self.assertIsNotNone(gs.players[0].hands[0].outcome)
        self.assertEqual(2, len(gs.players[0].hands[0].cards))
        self.assertGreaterEqual(len(gs.dealer.hands[0].cards), 2)

    def test_hit(self):
        gs = TestBjGameState._setup_game([100], [('7h', '4d'), ('Qs', '8s')])

        gs = gs.update(BjPlayerUpdate(BjPlayerActions.HIT, gs.players[0].id, 0))
        self.assertEqual(BjPhases.PLAY, gs.current_phase)
        self.assertEqual(3, len(gs.players[0].hands[0].cards))

        gs.players[0].hands[0].cards[2].face = 'K'
        gs = gs.update(BjPlayerUpdate(BjPlayerActions.HIT, gs.players[0].id, 0))
        self.assertEqual(BjPhases.END, gs.current_phase)
        self.assertEqual(BjHandOutcomes.LOST, gs.players[0].hands[0].outcome)
        self.assertEqual(4, len(gs.players[0].hands[0].cards))

    def test_hand_score(self):
        self.assertEqual(21, BjHand([Card(k) for k in ('Jh', 'Ad')]).score())
        self.assertEqual(13, BjHand([Card(k) for k in ('Jh', 'Ad', '2s')]).score())
        self.assertEqual(12, BjHand([Card(k) for k in ('Jh', 'Ad', 'As')]).score())
        self.assertEqual(12, BjHand([Card(k) for k in ('Ad', 'As')]).score())
        self.assertEqual(20, BjHand([Card(k) for k in ('Kd', 'Qs')]).score())

        self.assertEqual(True, BjHand([Card(k) for k in ('Jh', 'Ad')]).is_blackjack())
        self.assertEqual(False, BjHand([Card(k) for k in ('Kd', 'Qs')]).is_blackjack())

    def test_end_round(self):
        # Player blackjack
        gs = TestBjGameState._setup_game([100], [('Jh', 'Ad'), ('Qs', '8s')])
        gs = gs.update(BjPlayerUpdate(BjPlayerActions.STAND, gs.players[0].id, 0))
        self.assertEqual(BjHandOutcomes.WON, gs.players[0].hands[0].outcome)
        self.assertEqual(1150, gs.players[0].total_credit)

        # Player blackjack push
        gs = TestBjGameState._setup_game([100], [('Jh', 'Ad'), ('Qs', 'As')])
        gs = gs.update(BjPlayerUpdate(BjPlayerActions.STAND, gs.players[0].id, 0))
        self.assertEqual(BjHandOutcomes.PUSH, gs.players[0].hands[0].outcome)
        self.assertEqual(1000, gs.players[0].total_credit)

        # Dealer blackjack
        gs = TestBjGameState._setup_game([100], [('Jh', '9d', '2d'), ('Qs', 'As')])
        gs = gs.update(BjPlayerUpdate(BjPlayerActions.STAND, gs.players[0].id, 0))
        self.assertEqual(BjHandOutcomes.LOST, gs.players[0].hands[0].outcome)
        self.assertEqual(900, gs.players[0].total_credit)

        # Push
        gs = TestBjGameState._setup_game([100], [('Jh', '9d'), ('Qs', '9s')])
        gs = gs.update(BjPlayerUpdate(BjPlayerActions.STAND, gs.players[0].id, 0))
        self.assertEqual(BjHandOutcomes.PUSH, gs.players[0].hands[0].outcome)
        self.assertEqual(1000, gs.players[0].total_credit)

        # Basic win
        gs = TestBjGameState._setup_game([100], [('Jh', 'Kd'), ('Qs', '9s')])
        gs = gs.update(BjPlayerUpdate(BjPlayerActions.STAND, gs.players[0].id, 0))
        self.assertEqual(BjHandOutcomes.WON, gs.players[0].hands[0].outcome)
        self.assertEqual(1100, gs.players[0].total_credit)

        # Basic loss
        gs = TestBjGameState._setup_game([100], [('Jh', '8d'), ('Qs', '9s')])
        gs = gs.update(BjPlayerUpdate(BjPlayerActions.STAND, gs.players[0].id, 0))
        self.assertEqual(BjHandOutcomes.LOST, gs.players[0].hands[0].outcome)
        self.assertEqual(900, gs.players[0].total_credit)

        # Bust
        gs = TestBjGameState._setup_game([100], [('Jh', '8d', '5h'), ('Qs', '9s')])
        gs = gs.update(BjPlayerUpdate(BjPlayerActions.STAND, gs.players[0].id, 0))
        self.assertEqual(BjHandOutcomes.LOST, gs.players[0].hands[0].outcome)
        self.assertEqual(900, gs.players[0].total_credit)

        # Both bust
        gs = TestBjGameState._setup_game([100], [('Jh', '8d', '5h'), ('Qs', '6s', 'Jd')])
        gs = gs.update(BjPlayerUpdate(BjPlayerActions.STAND, gs.players[0].id, 0))
        self.assertEqual(BjHandOutcomes.LOST, gs.players[0].hands[0].outcome)
        self.assertEqual(900, gs.players[0].total_credit)

    @staticmethod
    def _setup_game(initial_bets=[], force_hands=None, initial_balance=1000):
        gs = BjGameState()

        for i in range(len(initial_bets)):
            gs = gs.update(BjPlayerUpdate(BjPlayerActions.JOIN, bet_amt=1000))

        for i, p in enumerate(gs.players):
            gs = gs.update(BjPlayerUpdate(BjPlayerActions.BET, player_id=p.id, hand_idx=0, bet_amt=initial_bets[i]))

        if force_hands is not None:
            gs.dealer.hands[0].cards = [Card(c) for c in force_hands.pop()]
            for i, cards in enumerate(force_hands):
                gs.players[i].hands[0].cards = [Card(c) for c in cards]

        return gs


if __name__ == '__main__':
    unittest.main()
