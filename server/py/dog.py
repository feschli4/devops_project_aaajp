# runcmd: cd ../.. & venv\Scripts\python server/py/dog_template.py
from typing import List, Optional, ClassVar, Union # corrected order of imports for pydantic
from enum import Enum
import random
from pydantic import BaseModel
from server.py.game import Game, Player


class Card(BaseModel):
    suit: str  # card suit (color)
    rank: str  # card rank


class Marble(BaseModel):
    pos: Optional[int] = None       # position on board (0 to 95)
    is_save: bool  # true if marble was moved out of kennel and was not yet moved


class PlayerState(BaseModel):
    name: str                  # name of player
    list_card: List[Card]      # list of cards
    list_marble: List[Marble]  # list of marbles


class Action(BaseModel):
    card: Card                 # card to play
    pos_from: Optional[int]    # position to move the marble from
    pos_to: Optional[int]      # position to move the marble to
    card_swap: Optional[Card] = None # optional card to swap ()


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

    PLAYER_BOARD_SEGMENTS = {
        0: {'start': 0, 'queue_start': 64, 'final_start': 68},
        1: {'start': 16, 'queue_start': 72, 'final_start': 76},
        2: {'start': 32, 'queue_start': 80, 'final_start': 84},
        3: {'start': 48, 'queue_start': 88, 'final_start': 92}
    }

    # Main path length (without final segment)
    MAIN_PATH_LENGTH = 64

    CARD_MOVEMENTS = {
        '2': 2,
        '3': 3,
        '4': -4,  # Rückwärtsbewegung
        '5': 5,
        '6': 6,
        '8': 8,
        '9': 9,
        '10': 10,
        'Q': 12,
        'K': 13,
        'J': None,  # Keine Bewegung, wird für Austausch genutzt
    }

    ACE_OPTIONS = [1, 11]  # Ace kann 1 oder 11 sein
    JOKER_OPTIONS = [1, 2, 3, 5, 6, 8, 9, 10, 12, 13]  # Joker ist flexibel
    SEVEN_OPTIONS = [1, 2, 3, 4, 5, 6, 7]  # Split-Möglichkeiten für SEVEN

    def __init__(self, cnt_players: int = 4) -> None:
        """ Game initialization (set_state call not necessary, we expect 4 players) """
        self.state: Optional[GameState] = None
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
            while len(player.list_card) < current_cards_count and self.state.list_card_draw:
                player.list_card.append(self.state.list_card_draw.pop())

        if not self.state.list_card_draw:
            self.state.list_card_draw = self.state.list_card_discard.copy()
            self.state.list_card_discard.clear()
            random.shuffle(self.state.list_card_draw)

    def next_turn(self) -> None:
        """ Advance the turn to the next player """
        self.state.idx_player_active = (self.state.idx_player_active + 1) % self.state.cnt_player

        # Überprüfen, ob alle Spieler gespielt haben, um die Runde zu erhöhen
        if self.state.idx_player_active == self.state.idx_player_started:
            self.state.cnt_round += 1
            self.setup_next_round()

    def _get_start_actions(self, card: Card, player: PlayerState) -> List[Action]:
        """Generiere Aktionen für Karten, die Marbles aus dem Kennel starten."""
        actions = []
        if card.rank in ['A', 'K', 'JKR']:
            for marble in player.list_marble:
                if marble.pos is None:  # Marble is in kennel
                    start_pos = self.PLAYER_BOARD_SEGMENTS[self.state.idx_player_active]['start']
                    if self.is_valid_move(None, start_pos):
                        actions.append(Action(card=card, pos_from=None, pos_to=start_pos))
        return actions

    def _get_standard_actions(self, card: Card, player: PlayerState, move_distance: Union[int, List[int]]) -> List[
        Action]:
        """Generiere Aktionen für Standardkarten."""
        actions = []
        if isinstance(move_distance, list):  # Mehrere Bewegungsmöglichkeiten (z.B. ACE, SEVEN)
            for distance in move_distance:
                for marble in player.list_marble:
                    if marble.pos is not None:
                        pos_to = (marble.pos + distance) % self.MAIN_PATH_LENGTH
                        if self.is_valid_move(marble.pos, pos_to):
                            actions.append(Action(card=card, pos_from=marble.pos, pos_to=pos_to))
        elif isinstance(move_distance, int):  # Einzelbewegung
            for marble in player.list_marble:
                if marble.pos is not None:
                    pos_to = (marble.pos + move_distance) % self.MAIN_PATH_LENGTH
                    if self.is_valid_move(marble.pos, pos_to):
                        actions.append(Action(card=card, pos_from=marble.pos, pos_to=pos_to))
        return actions

    def get_list_action(self) -> List[Action]:
        """ Get a list of possible actions for the active player """
        # ::TODO: Test 003-005 - Fetch valid actions based on cards in hand (get_valid_actions())
        possible_actions = []
        player = self.state.list_player[self.state.idx_player_active]

        for card in player.list_card:
            move_distance = self.get_move_distance(card)

            # Aktionen für Startkarten
            possible_actions.extend(self._get_start_actions(card, player))

            # Aktionen für Standardkarten
            if move_distance is not None:
                possible_actions.extend(self._get_standard_actions(card, player, move_distance))

        return possible_actions

    def is_valid_move(self, pos_from: int, pos_to: int) -> bool:
        """ Check if a move is valid """
        if pos_from is None:  # Start aus dem Kennel
            start_pos = self.PLAYER_BOARD_SEGMENTS[self.state.idx_player_active]['start']
            # Stelle sicher, dass die Startposition frei ist
            return pos_to == start_pos and all(
                marble.pos != start_pos for marble in self.state.list_player[self.state.idx_player_active].list_marble
            )
        # Standardbewegungen (z.B. keine Blockade)
        return True


    def apply_action(self, action: Action) -> None:
        """ Apply the given action to the game """
        if action is None:
            self.next_turn()  # Keine Aktion, überspringen
            return

        player = self.state.list_player[self.state.idx_player_active]

        if action.pos_from is None:  # Start aus dem Kennel
            marble = next((m for m in player.list_marble if m.pos is None), None)
        else:
            marble = next((m for m in player.list_marble if m.pos == action.pos_from), None)

        if marble is None:
            raise ValueError("Keine gültige Marble gefunden, die bewegt werden kann.")

        # Bewegung anwenden
        marble.pos = action.pos_to
        if action.pos_to == self.PLAYER_BOARD_SEGMENTS[self.state.idx_player_active]['start']:
            marble.is_save = True  # Marble ist sicher

        # Entferne die Karte und lege sie ab
        player.list_card.remove(action.card)
        self.state.list_card_discard.append(action.card)

        # Nächster Spieler
        self.next_turn()

    def check_game_status(self) -> None:
        """ Überprüft, ob das Spiel beendet ist """
        for player in self.state.list_player:
            if all(marble.pos is not None and marble.pos >= self.MAIN_PATH_LENGTH for marble in player.list_marble):
                self.state.phase = GamePhase.FINISHED
                print(f"Das Spiel ist beendet! Spieler {player.name} hat gewonnen.")


    def get_move_distance(self, card: Card) -> Optional[Union[int, List[int]]]:
        """
        Get the move distance based on the card rank. Implements special rules for ACE, SEVEN, and JOKER.
        """
        if card.rank in self.CARD_MOVEMENTS:
            return self.CARD_MOVEMENTS[card.rank]
        if card.rank == 'A':
            return self.ACE_OPTIONS
        if card.rank == '7':
            return self.SEVEN_OPTIONS
        if card.rank == 'JKR':
            return self.JOKER_OPTIONS

        # Standardfall: Ungültige Karte
        print(f"Warnung: Ungültige Karte {card.rank}. Keine Bewegung möglich.")
        return None

    def split_seven_move(self, steps: int) -> List[List[int]]:
        """Teilt die SEVEN-Karte in mögliche Bewegungen auf."""
        # ::TODO: Test 029-035 - Implement logic for splitting SEVEN card moves (move_with_seven_card())
        if steps != 7:
            raise ValueError("Nur 7 Schritte können gesplittet werden.")

        results = []

        def backtrack(path, remaining):
            if remaining == 0 and path:
                results.append(path[:])
                return
            for i in range(1, 8):  # Schritte von 1 bis 7
                if i > remaining:
                    break
                path.append(i)
                backtrack(path, remaining - i)
                path.pop()

        backtrack([], steps)
        return results

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

class RandomPlayer(Player):

    def select_action(self, state: GameState, actions: List[Action]) -> Optional[Action]:
        """ Given masked game state and possible actions, select the next action """
        if len(actions) > 0:
            return random.choice(actions)
        return None


if __name__ == '__main__':

    # Initialisiere das Spiel
    game = Dog()

    # 1. Initialen Spielstatus abrufen und ausgeben
    initial_state = game.get_state()
    print("Initialer Spielstatus:")
    print(initial_state)

    # 2. Nächste Runden vorbereiten und Kartenverteilung beobachten
    print("\nSimulation: Vorbereitung der nächsten Runden")
    for round_num in range(1, 4):
        game.setup_next_round()
        print(f"\nSpielstatus nach Vorbereitung der Runde {round_num + 1}:")
        print(game.get_state())

    # 3. Simulation einiger Spielzüge
    print("\nSimulation: Spielzüge")
    for turn in range(6):
        # Verfügbare Aktionen abrufen
        available_actions = game.get_list_action()
        if available_actions:
            # Wähle zufällig eine Aktion aus
            selected_action = random.choice(available_actions)
            game.apply_action(selected_action)
        else:
            # Wenn keine gültigen Aktionen verfügbar sind, den Zug überspringen
            game.next_turn()

        # Spielstatus nach dem Zug ausgeben
        print(f"\nSpielstatus nach Zug {turn + 1}:")
        print(game.get_state())

    # 4. Spiel zurücksetzen und Status ausgeben
    game.reset()
    print("\nSpielstatus nach Zurücksetzen:")
    print(game.get_state())
