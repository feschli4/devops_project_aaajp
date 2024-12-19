# Functions for Brandy Dog

## Class: dog

### new_round(self, rnd_nr: int) -> None
- **Description**: 
  - Set cnt_round +1.
  - Shuffle and draw (see functions below).
  - Set player 0 active. 

### new_turn(self) -> None
- **Description**: 
  - Reset card_active, seven_count


### shuffle(self) -> None
- **Description**: 
  - Reset cards (including drawn and discarded cards).
  - Randomize the sequence of cards in the deck.

### pick_exchange_card(self, player_id: int) -> None
- **Description**: 
  - Each player chooses the card they want to give their partner.
  - The exchange (separate function) happens after each player has chosen a card.

### get_list_action()
- **Desciption:**
  - If a card is active: only allow actions related to that card
  - Subfunctions: see card actions below

### apply_action(self) -> None
- **Description**: 
  - Execute the chosen action.
  - Subfunctions: Card specific functions, **set_move_target(self, card: Card, marble: Mable, pos: int)**, **next_turn()**

## Class: tile
 - **Desciption**
   - Attributes:
    - pos: int (1-96)
    - marble: marble or none
    - player_kenel: player or none
    - player_finish: player or none
    - player_start: player or none

### check_actions(self) -> None
- **Description**: 
  - If `len(list_actions) == 0`, the player can't do anything.
  - All their potentially remaining cards are discarded and they are skipped.
  - **Note**: Ensure there's no endless loop if all players run out of cards.


### check_finished(self) -> None
- **Description**: 
  - Check at the end of each turn if the player's and their partner's marbles are finished.

### check_team_win(self) -> None
- **Description**: 
  - Check at the end of each turn if the player and their partner have finished.
  - End the game if so.

### transfer_draw(self, no_cards: int, player_id: int) -> None
- **Description**: 
  - Draw X cards from the deck. X is {6 - ((cnt_round - 1) % 5)}

### transfer_exchange(self, player_id: int) -> None
- **Description**: 
  - The card marked for exchange is transferred to the player's partner.

### transfer_discard(self) -> None
- **Description**: 
  - A card goes from the player to the "discarded" pile.
  - Could be integrated into apply_action()

### move(self, pos_from: tile, pos_to: tile, marble: marble) -> None
- **Description**: 
  - Move Marble to a new position:
   - Change pos on marble
   - Remove Marble from pos_from tile
   - add marble to pos_to tile
   - if not ook-move (see below) or now in finish: 
      set marble.safe to FALSE
  - Apply "get_eaten" to marbles on the target position.

### switch(self, target_id: int) -> None
- **Description**: 
  - Chose other marble.
  - Switch positions of marles.

### get_eaten(self) -> None
- **Description**: 
  - Check if the marble is NOT safe.
  - If not safe, the marble is reset (goes back to its default position).

### check_if_in_final_area(self, marble_pos: int) -> bool:
- **Description**: 
  - Check if the marble is in final area and disable it if so.
  - Should probably tie into function "check_finished"

## Special Card Actions
(ook = "out of kenel")

### move_ook
 - get_list_action:
  - if card has ook-ability 
      for own marble in kenel:
        add [move marble to player's start tile] to action_list

 - apply_action:
   - send home potential occupying marble
   - move the marble
   - set marble to safe


### ace()
 - ook: **yes**

 - get_list_action:
  - for marble 
      for move in range(1:11):
        if pos_from+i is invalid: break
        elif move in [1,11]: add to action_list

 - apply_action:
   - for tile in range(pos_from, pos_to)   # don't forget about going over 0
     send home all marbles
   - move marble
   - new_turn


### king()
 - ook: **yes**

 - get_list_action:
   - check normal moves 

 - apply_action:
   - like in normal action


### queen()
 - normal move with 12...


### jack()
 - ook: no

 - get_list_action:
  - for own marble not in kenel and not in finish:
      for marble (all players):
        if marble not in kenel or not in finish or not original marble:
          add to action_list

 - apply_action:
  - jack_move marble: 
    1. normally move first marble
    2. move second marble without removing first marble from its new tile

### joker()
 - get_list_action:
  - for car in all cards:
    get_list_action

 - apply_action:
  - mimic chosen card

### four()
 - ook: no

 - get_list_action:
   1. forward_action like normal action
   2. backward_action like a normal action but with -1 per loop instead of +1

### seven()
 - change to gamestate:
  - add seven_moves (int or false)

 - ook: no

 - get_list_action:
  - like normal action but add every action to list_action
  - if seven_moves is not none use 7 for move_length

 - apply_action:
  1. Setup: if card_active = None then set card_active to card and seven_moves to 7
  2. move marble like normal move
  3. subtract move distance from seven_moves
  4. if seven_moves == 0 then set card_active to none and seven_moves to none
  5. if len(get_list_action) == 0 then new_round

### normal()
 - ook: no

 - get_list_action(value):
   - for own marble not in kenel:
      for move in range (1, value):
        if pos_from + move is not valid: break
        elif move == value:         # only add to action list after checking every tile 
          add to action_list

 - apply_action:
  - just a move...