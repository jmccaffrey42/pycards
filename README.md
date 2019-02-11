# Overview

PyCards is a card game simulation library written in Python (3.6). Currently PyCards implements standard BlackJack rules
and in the future might support more game types.

The library is designed to take in player updates objects and transform an immutable game state object with the update, 
or raise an exception if the update is invalid.

## Basic Operations

#### Deal 5 cards from 4 decks
```python
from pycards.deck import Deck
d = Deck(4) ## 4 decks deep
list(map(str, d.deal(5))) ## returns ['4d', '4s', 'Ks', '8d', '3d']
```

#### Create a BlacjJack hand and score it
```python
from pycards.blackjack import BjHand
from pycards.card import Card

h = BjHand([Card(k) for k in ('Qh', 'As')])
h.score() ## returns 21
h.is_blackjack() ## returns True
```

## Full BlackJack round
```python
from pycards.blackjack import BjGameState, BjPlayerUpdate, BjPlayerActions, BjPhases
gs = BjGameState()

## Both players start with 1000 credits
gs = gs.update(BjPlayerUpdate(BjPlayerActions.JOIN, bet_amt=1000))
gs = gs.update(BjPlayerUpdate(BjPlayerActions.JOIN, bet_amt=1000))

## Player 1 bets 100
gs = gs.update(BjPlayerUpdate(BjPlayerActions.BET, gs.players[0].id, 0, bet_amt=100))

## Player 2 bets 200
gs = gs.update(BjPlayerUpdate(BjPlayerActions.BET, gs.players[1].id, 0, bet_amt=200))

## Player 1 hits once
gs = gs.update(BjPlayerUpdate(BjPlayerActions.HIT, gs.players[0].id, 0))
gs = gs.update(BjPlayerUpdate(BjPlayerActions.STAND, gs.players[0].id, 0))

## Player 2 stands
gs = gs.update(BjPlayerUpdate(BjPlayerActions.STAND, gs.players[1].id, 0))

## The round is now over
assert(gs.current_phase == BjPhases.END)
```