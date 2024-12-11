# runcmd: cd ../.. & venv\Scripts\python server/py/dog_template.py
from server.py.game import Game, Player
from typing import List, Optional, ClassVar
from pydantic import BaseModel
from enum import Enum
import random


class Card(BaseModel):
    suit: str  # card suit (color)
    rank: str  # card rank


class Marble(BaseModel):
    pos: Optional[int] = None       # position on board (0 to 95)
    is_save: bool = False  # true if marble was moved out of kennel and was not yet moved


class PlayerState(BaseModel):
    name: str                  # name of player
    list_card: List[Card]      # list of cards
    list_marble: List[Marble]  # list of marbles


class Action(BaseModel):
    card: Card                 # card to play
    pos_from: Optional[int]    # position to move the marble from
    pos_to: Optional[int]      # position to move the marble to
    card_swap: Optional[Card]  # optional card to swap ()


class GamePhase(str, Enum):
    SETUP = 'setup'            # before the game has started
    RUNNING = 'running'        # while the game is running
    FINISHED = 'finished'      # when the game is finished


class GameState(BaseModel):

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
    list_card_draw: List[Card]         # list of cards to draw
    list_card_discard: List[Card]      # list of cards discarded
    card_active: Optional[Card]        # active card (for 7 and JKR with sequence of actions)


class Dog(Game):

    def __init__(self, cnt_players: int = 4) -> None:
        """ Game initialization (set_state call not necessary, we expect 4 players) """
        self.state = None
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
            list_card_draw=[],
            list_card_discard=[],
            card_active=None
        )

        # Initialize card deck (two packs of Bridge-cards)
        self.state.list_card_draw = GameState.LIST_CARD.copy()   # Two packs of cards
        random.shuffle(self.state.list_card_draw)  # Shuffle the deck

        # Set up players
        for idx in range(self.state.cnt_player):
            list_card = [self.state.list_card_draw.pop() for _ in range(6)]  # Draw 6 cards for each player
            list_marble = [Marble(pos=None, is_save=False) for _ in range(4)]  # All marbles start in kennel
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
        """ Get a list of possible actions for the active player """
        pass

    def apply_action(self, action: Action) -> None:
        """ Apply the given action to the game """
        if action is None:
            # print("No valid action provided. Skipping turn.")
            self.next_turn()
            return
        player = self.state.list_player[self.state.idx_player_active]
        # Remove the card from the player's hand
        player.list_card.remove(action.card)
        self.state.list_card_discard.append(action.card)
        # TODO:: Move the marble if applicable

        ###################
        #DA-40
        kennel_to_start = {
            64: 0, 65: 0, 66: 0, 67: 0,  # Blau
            88: 48, 89: 48, 90: 48, 91: 48,  # Gelb
            83: 32, 82: 32, 81: 32, 80: 32,  # Rot
            75: 16, 74: 16, 73: 16, 72: 16  # Grün
        }

        #dummy list (solange keine list_marble vorhanden)
        player.list_marble = [
            Marble(pos=64, is_save=False),  # Marble in der Startposition
            Marble(pos=65, is_save=False),  # Weitere Marble im Startbereich
            Marble(pos=66, is_save=False),  # Weitere Marble im Startbereich
            Marble(pos=67, is_save=False)  # Weitere Marble im Startbereich
        ]

        if action.pos_from in kennel_to_start and action.pos_to == kennel_to_start[action.pos_from]:
            # call function to move marble out of kennel
            self.move_marble_out_of_kennel(action)
        ###################

        # Advance to the next player
        self.next_turn()

    def get_player_view(self, idx_player: int) -> GameState:
        """ Get the masked state for the active player (e.g. the oppontent's cards are face down)"""
        pass

    def swap_cards(self, player1_idx: int, player2_idx: int, card1: Card, card2: Card) -> None:
        # Hole die Spielerobjekte
        player1 = self.state.list_player[player1_idx]
        player2 = self.state.list_player[player2_idx]

        # Überprüfe, ob Spieler 1 die angegebene Karte hat
        if card1 not in player1.list_card:
            raise ValueError(f"Player {player1_idx} does not have the card {card1}.")

        # Überprüfe, ob Spieler 2 die angegebene Karte hat
        if card2 not in player2.list_card:
            raise ValueError(f"Player {player2_idx} does not have the card {card2}.")

        # Entferne die Karte von Spieler 1 und füge sie zu Spieler 2 hinzu
        player1.list_card.remove(card1)
        player2.list_card.append(card1)

        # Entferne die Karte von Spieler 2 und füge sie zu Spieler 1 hinzu
        player2.list_card.remove(card2)
        player1.list_card.append(card2)

######### DA-40
    # def move_marble_out_of_kennel(self, action: Action) -> None:
    #     """
    #     Move a marble out of the kennel if the action and conditions are valid.
    #     """
    #     # Get the active player
    #     player = self.state.list_player[self.state.idx_player_active]
    #
    #     #################################################
    #     # Manuell changes -> just for testing!!!!
    #     if not any(card.rank == 'A' and card.suit == '♥' for card in player.list_card):
    #         # add heart ass to list_card if not available
    #         player.list_card.append(Card(rank='A', suit='♥'))
    #
    #
    #     marble = next((m for m in player.list_marble if m.pos == action.pos_from), None)
    #     if not marble:
    #         # add a marble if the list_marble is empty
    #         marble = Marble(pos=action.pos_from, is_save=False)
    #         player.list_marble = [marble]
    #
    #     ##########################
    #
    #         # Map kennel positions to start positions
    #     kennel_to_start = {
    #         64: 0, 65: 0, 66: 0, 67: 0,  # Blau
    #         88: 48, 89: 48, 90: 48, 91: 48,  # Gelb
    #         83: 32, 82: 32, 81: 32, 80: 32,  # Rot
    #         75: 16, 74: 16, 73: 16, 72: 16  # Grün
    #     }
    #
    #     # Validate the action
    #     if action.pos_from not in kennel_to_start:
    #         raise ValueError(f"Invalid kennel position: {action.pos_from}.")
    #     if action.pos_to != kennel_to_start[action.pos_from]:
    #         raise ValueError(
    #             f"Marble must move to the correct start position: {kennel_to_start[action.pos_from]}, not {action.pos_to}."
    #         )
    #
    #     # Validate the card
    #     if action.card.rank not in {'A', 'K'}:
    #         raise ValueError(f"Card {action.card.rank} cannot be used to move a marble out of the kennel.")
    #
    #     if action.card not in player.list_card:
    #         raise ValueError(f"Player {player.name} does not have the card {action.card.rank}.")
    #
    #     # Find and move the marble
    #     marble = next((m for m in player.list_marble if m.pos == action.pos_from), None)
    #     if not marble:
    #         raise ValueError(f"No marble found at kennel position {action.pos_from}.")
    #
    #     # Execute the action
    #     marble.pos = action.pos_to
    #     marble.is_save = True  # Mark the marble as safe after moving out
    #
    #     # Update card state
    #     player.list_card.remove(action.card)
    #     self.state.list_card_discard.append(action.card)

    def move_marble_out_of_kennel(self, action: Action, test_player: PlayerState = None, test_state: GameState = None) -> None:
        """
        Move a marble out of the kennel if the action and conditions are valid.
        """
        # Verwende den Testzustand, wenn er übergeben wurde
        state = test_state or self.state
        player = test_player or state.list_player[state.idx_player_active]

        # Map kennel positions to start positions
        if test_player:
            kennel_to_start = {
                64: 0, 65: 0, 66: 0, 67: 0,  # Blau
                88: 48, 89: 48, 90: 48, 91: 48,  # Gelb
                83: 32, 82: 32, 81: 32, 80: 32,  # Rot
                75: 16, 74: 16, 73: 16, 72: 16  # Grün
            }

        # Validate the action
            if action.pos_from not in kennel_to_start:
                raise ValueError(f"Invalid kennel position: {action.pos_from}.")
            if action.pos_to != kennel_to_start[action.pos_from]:
                raise ValueError(
                    f"Marble must move to the correct start position: {kennel_to_start[action.pos_from]}, not {action.pos_to}."
                )

        # Validate the card
            if action.card.rank not in {'A', 'K'}:
                raise ValueError(f"Card {action.card.rank} cannot be used to move a marble out of the kennel.")

            if action.card not in player.list_card:
                raise ValueError(f"Player {player.name} does not have the card {action.card.rank}.")

        # Find and move the marble
        marble = next((m for m in player.list_marble if m.pos == action.pos_from), None)
        if not marble:
            raise ValueError(f"No marble found at kennel position {action.pos_from}.")

        # Execute the action
        marble.pos = action.pos_to
        marble.is_save = True  # Mark the marble as safe after moving out

        # Update card state
        if test_player:
            player.list_card.remove(action.card)
            state.list_card_discard.append(action.card)

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
            game.next_turn()

        # Print the game state after each turn
        print(f"\nGame State after turn {turn + 1}:")
        print(game.get_state())

    # Reset the game and print the reset state
    game.reset()
    print("\nGame State after resetting:")
    print(game.get_state())