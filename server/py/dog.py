# runcmd: cd ../.. & venv\Scripts\python server/py/dog_template.py
from server.py.game import Game, Player
from typing import List, Optional, ClassVar
from pydantic import BaseModel
from enum import Enum
import random
from typing import Optional

kenel_positions = [64, 65, 66, 67, 72, 73, 74, 75, 80, 81, 82, 83, 88, 89, 90, 91]

class Card(BaseModel):
    suit: str  # card suit (color)
    rank: str  # card rank


class Marble(BaseModel):
    pos: Optional[int] = None       # position on board (0 to 95)
    is_save: bool  # true if marble was moved out of kennel and was not yet moved
    is_finished: bool


class PlayerState(BaseModel):
    name: str                  # name of player
    list_card: List[Card]      # list of cards
    list_marble: List[Marble]  # list of marbles


class Action(BaseModel):
    card: Card                 # card to play
    pos_from: Optional[int]    # position to move the marble from
    pos_to: Optional[int]      # position to move the marble to
    card_swap: Optional[Card]  # optional card to swap ()


class Field(BaseModel):
    idx: int
    occupied: bool
    occupying_player: Optional[int] = None
    occupying_marble: Optional[Marble] = None


class GamePhase(str, Enum):
    SETUP = 'setup'            # before the game has started
    RUNNING = 'running'        # while the game is running
    FINISHED = 'finished'      # when the game is finished


class GameState(BaseModel):
    LIST_FIELD: ClassVar[List[Field]] = [
        Field(
            idx=i,
            occupied=False,
            occupying_player=None,
            occupying_marble=None
        )
        for i in range(96)
    ]

    LIST_SUIT: ClassVar[List[str]] = ['♠', '♥', '♦', '♣']  # 4 suits (colors)
    LIST_RANK: ClassVar[List[str]] = [
        '2', '3', '4', '5', '6', '7', '8', '9', '10',      # 13 ranks + Joker
        'J', 'Q', 'K', 'A', 'JKR'
    ]
    LIST_CARD: ClassVar[List[Card]] = [
        # 2: Move 2 spots forward
        Card(suit='♠', rank='2'), Card(suit='♥', rank='2'), Card(suit='♦', rank='2'), Card(suit='♣', rank='2'),
        # 3: Move 3 spots forward
        Card(suit='♠', rank='3'), Card(suit='♥', rank='3'), Card(suit='♦', rank='3'), Card(suit='♣', rank='3'),
        # 4: Move 4 spots forward or back
        Card(suit='♠', rank='4'), Card(suit='♥', rank='4'), Card(suit='♦', rank='4'), Card(suit='♣', rank='4'),
        # 5: Move 5 spots forward
        Card(suit='♠', rank='5'), Card(suit='♥', rank='5'), Card(suit='♦', rank='5'), Card(suit='♣', rank='5'),
        # 6: Move 6 spots forward
        Card(suit='♠', rank='6'), Card(suit='♥', rank='6'), Card(suit='♦', rank='6'), Card(suit='♣', rank='6'),
        # 7: Move 7 single steps forward
        Card(suit='♠', rank='7'), Card(suit='♥', rank='7'), Card(suit='♦', rank='7'), Card(suit='♣', rank='7'),
        # 8: Move 8 spots forward
        Card(suit='♠', rank='8'), Card(suit='♥', rank='8'), Card(suit='♦', rank='8'), Card(suit='♣', rank='8'),
        # 9: Move 9 spots forward
        Card(suit='♠', rank='9'), Card(suit='♥', rank='9'), Card(suit='♦', rank='9'), Card(suit='♣', rank='9'),
        # 10: Move 10 spots forward
        Card(suit='♠', rank='10'), Card(suit='♥', rank='10'), Card(suit='♦', rank='10'), Card(suit='♣', rank='10'),
        # Jake: A marble must be exchanged
        Card(suit='♠', rank='J'), Card(suit='♥', rank='J'), Card(suit='♦', rank='J'), Card(suit='♣', rank='J'),
        # Queen: Move 12 spots forward
        Card(suit='♠', rank='Q'), Card(suit='♥', rank='Q'), Card(suit='♦', rank='Q'), Card(suit='♣', rank='Q'),
        # King: Start or move 13 spots forward
        Card(suit='♠', rank='K'), Card(suit='♥', rank='K'), Card(suit='♦', rank='K'), Card(suit='♣', rank='K'),
        # Ass: Start or move 1 or 11 spots forward
        Card(suit='♠', rank='A'), Card(suit='♥', rank='A'), Card(suit='♦', rank='A'), Card(suit='♣', rank='A'),
        # Joker: Use as any other card you want
        Card(suit='', rank='JKR'), Card(suit='', rank='JKR'), Card(suit='', rank='JKR')
    ] * 2

    cnt_player: int = 4                # number of players (must be 4)
    phase: GamePhase                   # current phase of the game
    cnt_round: int                     # current round
    bool_card_exchanged: bool          # true if cards was exchanged in round
    idx_player_started: int            # index of player that started the round
    idx_player_active: int             # index of active player in round
    list_player: List[PlayerState]     # list of players
    list_fields: List[Field]
    list_card_draw: List[Card]         # list of cards to draw
    list_card_discard: List[Card]      # list of cards discarded
    card_active: Optional[Card]        # active card (for 7 and JKR with sequence of actions)
    seven_steps_left: Optional[int]    # keeps track how many steps are left when a seven is plaid


class Dog(Game):

    def __init__(self, cnt_players: int = 4) -> None:
        """ Game initialization (set_state call not necessary, we expect 4 players) """
        self._initialize_game(cnt_players)

    def _initialize_game(self, cnt_players: int) -> None:
        """Initialize the game to its starting state"""
        if cnt_players not in [4]:
            raise ValueError("The game must be played with 4 players.")

        self.state = GameState(
            cnt_player=cnt_players,
            phase=GamePhase.SETUP,
            cnt_round=1,
            bool_card_exchanged=False,
            idx_player_started=0,
            idx_player_active=0,
            list_player=[],
            list_fields=[],
            list_card_draw=[],
            list_card_discard=[],
            card_active=None,
            seven_steps_left=None
        )
        # Initialize fields
        self.state.list_fields = GameState.LIST_FIELD.copy()
        # Initialize card deck (two packs of Bridge-cards)
        self.state.list_card_draw = GameState.LIST_CARD.copy()   # Two packs of cards
        random.shuffle(self.state.list_card_draw)  # Shuffle the deck

        # Set up players
        for idx in range(self.state.cnt_player):
            list_card = [self.state.list_card_draw.pop() for _ in range(6)]  # Draw 6 cards for each player
            list_marble = [Marble(pos=None, is_save=False, is_finished=False) for _ in range(4)]  # All marbles start in kennel
            player_state = PlayerState(name=f"Player {idx + 1}", list_card=list_card, list_marble=list_marble)
            self.state.list_player.append(player_state)

        # Randomly select the player who starts
        self.state.idx_player_started = random.randint(0, self.state.cnt_player - 1)
        self.state.idx_player_active = self.state.idx_player_started

        # Update the game phase after setup
        self.state.phase = GamePhase.RUNNING
        self.state.bool_card_exchanged = False  # Reset card exchange flag at the beginning

    def reset(self) -> None:
        """Setzt das Spiel in den Ausgangszustand zurück"""
        self._initialize_game(self.state.cnt_player)

    def set_state(self, state: GameState) -> None:
        """ Set the game to a given state """
        self.state = state

    def get_state(self) -> GameState:
        """ Get the complete, unmasked game state """
        return self.state

    def print_state(self) -> None:
        """ Print the current game state """
        pass

    def setup_next_round(self) -> None:
        """ Setup the next round with decreasing number of cards """
        cards_in_round = [6, 5, 4, 3, 2]  # Anzahl der Karten für jede Runde (beginnend mit Runde 1)
        current_cards_count = cards_in_round[(self.state.cnt_round - 1) % len(cards_in_round)]
        # Deal cards to each player
        for player in self.state.list_player:
            player.list_card = [self.state.list_card_draw.pop() for _ in range(current_cards_count) if
                                self.state.list_card_draw]
        # TODO:: Test re-shuffle if stock out of cards (list_card_draw)

    def next_turn(self) -> None:
        """ Advance the turn to the next player """
        self.state.idx_player_active = (self.state.idx_player_active + 1) % self.state.cnt_player
        # If all players have played, increase the round count
        if self.state.idx_player_active == self.state.idx_player_started:
            self.state.cnt_round += 1
            # self.exchange_cards() # TODO:: Exchange cards between players
            self.setup_next_round()  # Setup the next round with updated card counts

    def get_list_action(self) -> List[Action]:
        player = self.state.list_player[self.state.idx_player_active]
        possible_actions = []
        if self.state.card_active is not None:
            # Special actions for the seven card
            if self.state.card_active.rank == '7':
                possible_actions.extend(
                    self.get_list_seven_actions(self.state.card_active, self.state.seven_steps_left))
            else:
                pass
        elif player.list_card:  # If player has cards left...
            for card in player.list_card:  # Check all cards
                if card.rank == '7':
                    possible_actions.extend(self.get_list_seven_actions(self.state.card_active))
        return possible_actions

    def get_list_seven_actions(self, card, moves_left=7):
        player = self.state.list_player[self.state.idx_player_active]
        player_number = self.state.idx_player_active + 1
        player_start_field = (player_number - 1) * 16
        player_first_finish_field = player_number * 8 + 60
        seven_actions = []
        for marble in player.list_marble:
            # I keep track on which step a marble passes the player's start field
            step_passed_start_field = 0 if (marble.pos == player_start_field and not marble.is_save) else None
            if marble.pos is not None and not marble.is_finished and marble.pos not in kenel_positions:
                move_from = marble.pos
                valid_target_fields = []

                # First find valid target fields outside the finish zone
                for step in range(1, moves_left + 1):
                    move_to = (move_from + step) % 64
                    # Check again if this passes the start field
                    step_passed_start_field = step if (move_to == player_start_field) else step_passed_start_field
                    if (self.state.list_fields[move_to].occupying_marble is None
                            or not self.state.list_fields[move_to].occupying_marble.is_save):
                        valid_target_fields.append(move_to)
                    else:
                        break
                # Check for valid target fields inside the finish zone
                if step_passed_start_field is not None and step_passed_start_field < moves_left:
                    moves_left_in_finish_zone = moves_left - step_passed_start_field
                    for field in range(player_first_finish_field, player_first_finish_field + 4):
                        if ((field - player_first_finish_field) > moves_left_in_finish_zone
                                or self.state.list_fields[field].occupied):
                            break
                        else:
                            valid_target_fields.append(field)

                for target_field in valid_target_fields:
                    seven_actions.append(Action(card=card, pos_from=marble.pos, pos_to=target_field))
        return seven_actions

    def apply_action(self, action: Action) -> None:
        """ Apply the given action to the game """
        player_number = self.state.idx_player_active + 1
        if action is None:
            print("No valid action provided. Skipping turn.")
            self.next_turn()
            return
        player = self.state.list_player[self.state.idx_player_active]

        if action.card.rank == '7':
            # Set up everything
            if self.state.card_active is None:
                self.state.card_active = action.card
                self.state.seven_steps_left = 7

            # When moving with a seven, ALL overtaken marbles get sent home (including your own).
            # Check if marble crosses "zero" field
            if action.pos_from > action.pos_to:
                for tile in range(action.pos_from + 1, 64):
                    self.send_marble_home(tile)
                    self.state.seven_steps_left -= 1

                for tile in range(0, action.pos_to + 1):
                    self.send_marble_home(tile)
                    self.state.seven_steps_left -= 1

            # When moving to a finish field
            elif action.pos_to > 64 and action.pos_from < 68:
                # Tiles from pos_from to the player's start field
                for tile in range(action.pos_from + 1, (player_number - 1) * 16 + 1):
                    self.send_marble_home(tile)
                    self.state.seven_steps_left -= 1

                # Tiles inside the finish zone
                for tile in range(player_number * 8 + 60, action.pos_to+1): # Each player's lowest finish
                    self.send_marble_home(tile)
                    self.state.seven_steps_left -= 1

            # Standard move
            else:
                for tile in range(action.pos_from + 1, action.pos_to+1):
                    self.send_marble_home(tile)
                    self.state.seven_steps_left -= 1

            # Check if seven should be deactivated
            list_action_found = self.get_list_action()
            if self.state.seven_steps_left == 0 or len(list_action_found) == 0:
                self.state.seven_steps_left = None
                self.state.card_active = None

                # Remove the seven card from the player's hand
                player.list_card.remove(action.card)
                self.state.list_card_discard.append(action.card)

            # Move Marble to new field
            self.regular_move(action.pos_from, action.pos_to)

        # TODO:: Move the marble if applicable
        # Can only advance if no card is active
        if self.state.card_active is None:
            # Advance to the next player
            print('all is done, next player')
            self.next_turn()

    def get_player_view(self, idx_player: int) -> GameState:
        """ Get the masked state for the active player (e.g. the oppontent's cards are face down)"""
        pass

    def send_marble_home(self, tile):
        """Send the marble occupying the given tile home."""
        occupying_marble = None
        marble_list = self.get_marble_list()
        # If tile is occupied...
        for marble in marble_list:
            if marble.pos == tile:
                occupying_marble = marble
        if occupying_marble is not None:
            # ... find the occupying marble's owner
            player = self.get_marble_owner(occupying_marble)
            player_number = int(player.name[-1])
            # ... find his first free kenel field
            first_kenel_field = 64 + (player_number-1) * 8
            first_free_kenel_field = next(i for i in range(first_kenel_field, first_kenel_field + 4)
                                          if not self.state.list_fields[i].occupied)
            # ...send the marble home
            self.regular_move(tile, first_free_kenel_field)

    def regular_move(self, pos_from, pos_to):
        from_field = self.state.list_fields[pos_from]
        to_field = self.state.list_fields[pos_to]

        # Since benchmark does not modify our selfmade fields, we need to iterate through all marbles.
        # It's important for the send_home function
        marble_list = self.get_marble_list()
        marble = next((marble for marble in marble_list if marble.pos == pos_from), None)
        # Move Marble to new field
        marble.pos = pos_to

        player = self.get_marble_owner(marble)

        # Clear old field
        from_field.occupying_marble = None
        from_field.occupied = False
        from_field.occupying_player = None

        # Add to new Field
        to_field.occupying_marble = marble
        to_field.occupied = True
        to_field.occupying_player = player

    def get_marble_list(self):
        marble_list = []
        for player in self.state.list_player:
            marble_list.extend(player.list_marble)
        return marble_list

    def get_marble_owner(self,marble):
        owner = None
        for player in self.state.list_player:
            if marble in player.list_marble:
                owner = player
                break
        return owner


class RandomPlayer(Player):

    def select_action(self, state: GameState, actions: List[Action]) -> Optional[Action]:
        """ Given masked game state and possible actions, select the next action """
        if len(actions) > 0:
            return random.choice(actions)
        return None


if __name__ == '__main__':

    game = Dog()

    # Get the initial state of the game and print it
    initial_state = game.get_state()
    print("Initial Game State:")
    print(initial_state)

    # Simulate setting up the next rounds to see how the card distribution changes
    for round_num in range(1, 4):
        game.setup_next_round()
        print(f"\nGame State after setting up round {round_num + 1}:")
        print(game.get_state())

    # Simulate a few turns to see how the game progresses
    print("\nStarting turns simulation:")
    for turn in range(6):
        # Example of getting available actions (currently, not implemented)
        actions = game.get_list_action()
        if actions:
            # Apply a random action (using RandomPlayer logic as an example)
            action = random.choice(actions)
            game.apply_action(action)
        else:
            # If no valid actions, skip the turn
            print("no valid actions - next turn")
            game.next_turn()

        # Print the game state after each turn
        print(f"\nGame State after turn {turn + 1}:")
        print(game.get_state())

    # Reset the game and print the reset state
    game.reset()
    print("\nGame State after resetting:")
    print(game.get_state())