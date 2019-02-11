import copy
import math
from enum import Enum

from pycards.deck import Deck


TEN_CARDS = ['10', 'J', 'Q', 'K']


class BjGameError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class BjPlayerActions(Enum):
    STAND = 1
    HIT = 2
    DOUBLE = 3
    SPLIT = 4
    SURRENDER = 5
    INSURANCE = 6
    BET = 7
    JOIN = 8


class BjHandOutcomes(Enum):
    WON = 1
    LOST = 2
    PUSH = 3


class BjPhases(Enum):
    BET = 0
    PLAY = 1
    END = 2
    INSURANCE = 4


class BjPlayerUpdate:
    def __init__(self, action, player_id=None, hand_idx=None, bet_amt=None):
        self.action = action
        self.player_id = player_id
        self.hand_idx = hand_idx
        self.bet_amt = bet_amt


class BjPlayer:
    def __init__(self, id, total_credit=0, hands=list(), insurance_bet=0):
        self.id = id
        self.total_credit = total_credit
        self.hands = hands
        self.insurance_bet = insurance_bet


class BjHand:
    def __init__(self, cards=list(), bet_amt=0, has_doubled=False, is_out=False, outcome=None):
        self.cards = cards
        self.bet_amt = bet_amt
        self.has_doubled = has_doubled
        self.is_out = is_out
        self.outcome = outcome

    def score(self):
        def card_points(c):
            if c.face == 'A':
                return 0
            elif c.face in TEN_CARDS:
                return 10
            else:
                return int(c.face)

        num_aces = len(list(filter(lambda c: c.face == 'A', self.cards)))
        pre_ace_total = sum(map(card_points, self.cards))

        high_aces = 0
        if num_aces > 0 and pre_ace_total <= 10 - (num_aces - 1):
            num_aces -= 1
            high_aces = 1

        return pre_ace_total + high_aces * 11 + num_aces

    def is_blackjack(self):
        hand_faces = sorted(list(map(lambda c: c.face, self.cards)))
        return len(hand_faces) == 2 and hand_faces[0] == 'A' and hand_faces[1] in TEN_CARDS


class BjGameState:
    def __init__(self):
        self.players = list()
        self.dealer = BjPlayer(-1)
        self.deck = Deck(6)
        self.current_turn_player_id = 0
        self.current_phase = BjPhases.END
        self._player_counter = 0

    def update(self, player_update):

        apply_fn = {
            BjPlayerActions.STAND: BjGameState._apply_stand,
            BjPlayerActions.HIT: BjGameState._apply_hit,
            BjPlayerActions.DOUBLE: BjGameState._apply_double,
            BjPlayerActions.SPLIT: BjGameState._apply_split,
            BjPlayerActions.SURRENDER: BjGameState._apply_surrender,
            BjPlayerActions.INSURANCE: BjGameState._apply_insurance,
            BjPlayerActions.BET: BjGameState._apply_bet,
            BjPlayerActions.JOIN: BjGameState._apply_join
        }

        if player_update.action not in apply_fn:
            raise(BjGameError('unknown action {}'.format(player_update.action)))

        if player_update.action != BjPlayerActions.JOIN and player_update.player_id != self.current_turn_player_id:
            raise(BjGameError('it is not this players turn'))

        if player_update.hand_idx is None and player_update.action not in [BjPlayerActions.JOIN, BjPlayerActions.INSURANCE]:
            raise(BjGameError('missing required hand_id for this action'))

        new_state = copy.deepcopy(self)

        apply_fn[player_update.action](new_state, player_update)

        return new_state

    def _apply_stand(self, player_update):
        self._end_turn()

    def _apply_hit(self, player_update):
        (p, h) = self._get_player_and_hand(player_update)

        h.cards.append(self.deck.deal(1)[0])
        if h.score() > 21:
            self._end_turn()

    def _apply_double(self, player_update):
        pass

    def _apply_split(self, player_update):
        pass

    def _apply_surrender(self, player_update):
        pass

    def _apply_insurance(self, player_update):
        pass

    def _apply_bet(self, player_update):
        if self.current_phase == BjPhases.END:
            self._start_round()
        elif self.current_phase != BjPhases.BET:
            raise(BjGameError('cannot bet outside of the bet phase'))

        (p, h) = self._get_player_and_hand(player_update)

        if p.total_credit < player_update.bet_amt:
            raise(BjGameError('insufficient funds to place bet'))

        p.total_credit -= player_update.bet_amt
        h.bet_amt += player_update.bet_amt

        self._end_turn()

    def _apply_join(self, player_update):
        if self.current_phase not in [BjPhases.BET, BjPhases.END]:
            raise(BjGameError('cannot join the game outside of the bet or end phase'))

        self._player_counter += 1
        if len(self.players) == 0:
            self.current_turn_player_id = self._player_counter

        self.players.append(BjPlayer(self._player_counter, player_update.bet_amt))

    def _get_player_and_hand(self, player_update):
        for p in self.players:
            if p.id == player_update.player_id:
                if len(p.hands) > player_update.hand_idx >= 0:
                    return (p, p.hands[player_update.hand_idx])

    def _start_round(self):
        self.current_phase = BjPhases.BET

        for p in self.players:
            p.insurance_bet = 0
            p.hands.clear()
            p.hands.append(BjHand())

        self.dealer.hands.clear()
        self.dealer.hands.append(BjHand())

    def _end_turn(self):
        try:
            next_player = next(filter(lambda p: p.id > self.current_turn_player_id, self.players))
            self.current_turn_player_id = next_player.id
        except StopIteration:
            # Getting here means all other players have played and its the dealer's turn
            if self.current_phase == BjPhases.BET:
                self._deal_players()
                if self.dealer.hands[0].cards[0].face == 'A':
                    self.current_phase = BjPhases.INSURANCE
                else:
                    self.current_phase = BjPhases.PLAY
            elif self.current_phase == BjPhases.PLAY:
                self._dealer_play()
                self._end_round()
            elif self.current_phase == BjPhases.INSURANCE:
                if self.dealer.hands[0].is_blackjack():
                    self._end_round()
                else:
                    self.current_phase = BjPhases.PLAY

            self.current_turn_player_id = min([p.id for p in self.players])

    def _dealer_play(self):
        dealer_hand = self.dealer.hands[0]

        score = dealer_hand.score()
        while score < 17:
            dealer_hand.cards.append(self.deck.deal(1)[0])
            score = dealer_hand.score()

    def _end_round(self):
        self.current_phase = BjPhases.END

        dealer_hand = self.dealer.hands[0]
        dealer_score = dealer_hand.score()
        dealer_blackjack = dealer_hand.is_blackjack()

        for p in self.players:

            for h in p.hands:
                payout = 0
                hand_score = h.score()
                hand_blackjack = h.is_blackjack()
                h.outcome = BjHandOutcomes.LOST

                if hand_score <= 21:
                    if hand_score > dealer_score:
                        h.outcome = BjHandOutcomes.WON
                        if hand_blackjack:
                            payout = math.ceil(h.bet_amt * 5/2)
                        else:
                            payout = h.bet_amt * 2
                    elif hand_score == dealer_score:
                        if dealer_blackjack == hand_blackjack:
                            h.outcome = BjHandOutcomes.PUSH
                            payout = h.bet_amt
                    elif dealer_score > 21:
                        h.outcome = BjHandOutcomes.WON
                        payout = h.bet_amt * 2

                p.total_credit += payout

            if dealer_blackjack and p.insurance_bet > 0:
                p.total_credit += p.insurance_bet * 2

    def _deal_players(self):
        for p in self.players:
            p.hands[0].cards = self.deck.deal(2)

        self.dealer.hands[0].cards = self.deck.deal(2)
