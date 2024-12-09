import pytest
import random
from server.py.dog import Dog, Card, Marble, PlayerState, Action, GameState, GamePhase



def test_swap_cards():
    game_state = GameState(
        list_player=[
            PlayerState(name="Player 1", list_card=[
                Card(suit="♠", rank="A"),  # Karte 1
                Card(suit="♥", rank="K"),  # Karte 2
                Card(suit="♦", rank="5"),  # Karte 3
                Card(suit="♣", rank="10"),  # Karte 4
                Card(suit="♠", rank="3")  # Karte 5
            ], list_marble=[]),
            PlayerState(name="Player 2", list_card=[
                Card(suit="♣", rank="7"),  # Karte 1
                Card(suit="♦", rank="2"),  # Karte 2
                Card(suit="♠", rank="9"),  # Karte 3
                Card(suit="♥", rank="Q"),  # Karte 4
                Card(suit="♦", rank="8")  # Karte 5
            ], list_marble=[])
        ],
        phase=GamePhase.RUNNING,
        cnt_round=1,
        bool_card_exchanged=False,
        idx_player_started=0,
        idx_player_active=0,
        list_card_draw=[],
        list_card_discard=[],
        card_active=None
    )

    # Create an instance of Dog and set the game state
    dog_game = Dog()
    dog_game.set_state(game_state)

    # Wähle explizit Karte 3 von Spieler 2 (♠ 9) und Karte 5 von Spieler 1 (♠ 3)
    card_player1_to_swap = dog_game.state.list_player[0].list_card[4]  # ♠ 3
    card_player2_to_swap = dog_game.state.list_player[1].list_card[2]  # ♠ 9

    # Führe den Kartentausch durch
    dog_game.swap_cards(player1_idx=0, player2_idx=1, card1=card_player1_to_swap, card2=card_player2_to_swap)

    # Assertions: Überprüfe, ob die Karte aus der Hand von Player 1 entfernt wurde und zu Player 2 hinzugefügt wurde
    assert card_player1_to_swap not in dog_game.state.list_player[
        0].list_card, f"Card {card_player1_to_swap} not removed from Player 1's hand"
    assert card_player1_to_swap in dog_game.state.list_player[
        1].list_card, f"Card {card_player1_to_swap} not added to Player 2's hand"

    # Überprüfe nun, dass die getauschte Karte von Player 2 auch in Player 1's Hand ist
    assert card_player2_to_swap not in dog_game.state.list_player[
        1].list_card, f"Card {card_player2_to_swap} not removed from Player 2's hand"
    assert card_player2_to_swap in dog_game.state.list_player[
        0].list_card, f"Card {card_player2_to_swap} not added to Player 1's hand"


@pytest.fixture
def game():
    return Dog()

def test_initialize_game():
    """Test initializing the Dog game."""
    game = Dog()
    state = game.get_state()
    assert state is not None
    assert len(state.list_player) == 4
    assert state.phase == GamePhase.RUNNING
    assert state.cnt_round == 1

def test_initial_game_state_values(game):
    """Test 001: Validate values of initial game state (cnt_round=1) [5 points]"""
    state = game.get_state()

    assert state.phase == GamePhase.RUNNING, f'{state}Error: "phase" must be GamePhase.RUNNING initially'
    assert state.cnt_round == 1, f'{state}Error: "cnt_round" must be 1 initially'
    assert len(state.list_card_discard) == 0, f'{state}Error: len("list_card_discard") must be 0 initially'
    assert len(state.list_card_draw) == 86, f'{state}Error: len("list_card_draw") must be 86 initially'
    assert len(state.list_player) == 4, f'{state}Error: len("list_player") must be 4'
    assert state.idx_player_active >= 0, f'{state}Error: "idx_player_active" must be >= 0'
    assert state.idx_player_active < 4, f'{state}Error: "idx_player_active" must be < 4'
    assert state.idx_player_started == state.idx_player_active, f'{state}Error: "idx_player_active" must be == "idx_player_started"'
    assert state.card_active is None, f'{state}Error: "card_active" must be None'
    assert not state.bool_card_exchanged, f'{state}Error: "bool_card_exchanged" must be False'

    for player in state.list_player:
        assert len(player.list_card) == 6, f'{state}Error: len("list_player.list_card") must be 6 initially'
        assert len(player.list_marble) == 4, f'{state}Error: len("list_player.list_marble") must be 4 initially'

def test_starting_player_is_active(game):
    """Test 002: Verify that the correct player starts the game [5 points]"""
    state = game.get_state()
    assert 0 <= state.idx_player_started < 4, f'{state}Error: "idx_player_started" must be in range (0-3)'
    assert state.idx_player_active == state.idx_player_started, f'{state}Error: "idx_player_active" must be equal to "idx_player_started" initially'

def test_set_custom_game_state():
    """Test 003: Set and validate a custom game state [5 points]"""
    game = Dog()
    new_state = GameState(
        cnt_player=4,
        phase=GamePhase.RUNNING,
        cnt_round=2,
        bool_card_exchanged=True,
        idx_player_started=1,
        idx_player_active=2,
        list_player=[
            PlayerState(name="Player 1", list_card=[], list_marble=[Marble(pos=None, is_save=False) for _ in range(4)]),
            PlayerState(name="Player 2", list_card=[], list_marble=[Marble(pos=None, is_save=False) for _ in range(4)]),
            PlayerState(name="Player 3", list_card=[], list_marble=[Marble(pos=None, is_save=False) for _ in range(4)]),
            PlayerState(name="Player 4", list_card=[], list_marble=[Marble(pos=None, is_save=False) for _ in range(4)])
        ],
        list_card_draw=[],
        list_card_discard=[],
        card_active=None
    )

    game.set_state(new_state)
    state = game.get_state()

    assert state.cnt_round == 2, f'{state}Error: "cnt_round" must be 2'
    assert state.idx_player_active == 2, f'{state}Error: "idx_player_active" must be 2'

def test_initial_marble_positions(game):
    """Test 004: Validate initial positions of all marbles [5 points]"""
    state = game.get_state()
    for player in state.list_player:
        for marble in player.list_marble:
            assert marble.pos is None, f'{state}Error: "marble.pos" must be None initially'
            assert not marble.is_save, f'{state}Error: "marble.is_save" must be False initially'

def test_initial_card_draw_pile(game):
    """Test 005: Validate the number of cards in the draw pile after initial deal [5 points]"""
    state = game.get_state()
    assert len(state.list_card_draw) == 86, f'{state}Error: "list_card_draw" must contain 86 cards initially'


def test_card_distribution_and_rounds():
    """Test006: Kartenverteilung und Simulation von 6 Runden"""
    # ::TODO 046-049 noch nicht konsitent (wohl ein Fehler in der action/setup_next_round oder inizialisierung und reshuffle funktioniert nicht)
    # ::TODO Runden pro spieler im Moment eine Aktion pro Spieler. Eventuell ändern auf aktionen bis keine mehr geht aber auch immer in gleicher Reihefolge
    print("""
            Start Game
              ↓
            Initialize Game State
              ↓
            Round 1:
              Player 1's Turn:
                ↓
                Check Available Actions:
                  - Move Marble
                  - Play Card
                  - If no valid actions → Discard Cards
                ↓
                Play Action:
                  - Apply Move
                  - Remove Played Card from Hand → Add to Discard Pile
                  - Check if Draw Pile is Empty → Reshuffle Discard Pile
                ↓
                If Actions Remaining → Continue Turn
                Else → Next Player
              ↓
              Player 2's Turn → Repeat
              ↓
              Player 3's Turn → Repeat
              ↓
              Player 4's Turn → Repeat
              ↓
            End of Round 1
              ↓
            Setup Next Round:
              - Decrease Cards Dealt Per Player
              - Reshuffle Draw Pile if Necessary
              - Deal Cards to Players
              ↓
            Check if Game Finished? --- No → Round 2
              ↓
            Round 2 → Repeat Player Turns
              ↓
            Check if Game Finished? --- No → Round 3
              ↓
            Round 3 → Repeat Player Turns
              ↓
            Check if Game Finished? --- Yes
              ↓
            Declare Winner
              ↓
            Reset Game State
              ↓
            End
            """)

    game = Dog()

    # Debugging: Überprüfung der Kartenverteilung
    def debug_card_distribution():
        state = game.get_state()
        draw_count = len(state.list_card_draw)
        discard_count = len(state.list_card_discard)
        hand_counts = [len(player.list_card) for player in state.list_player]
        total_cards = draw_count + discard_count + sum(hand_counts)
        print(f"Draw Pile: {draw_count}, Discard Pile: {discard_count}, Hands: {hand_counts}")
        print(f"Total Cards: {total_cards} (Expected: {len(GameState.LIST_CARD)})")
        assert total_cards == len(GameState.LIST_CARD), \
            f"Fehler: Kartenanzahl stimmt nicht überein. Erwartet: {len(GameState.LIST_CARD)}, Gefunden: {total_cards}"

    # Überprüfung der Kartenverteilung nach Initialisierung
    print("\n--- Überprüfung der Kartenverteilung nach Initialisierung ---")
    debug_card_distribution()

    # Simulation: Mehrere Runden spielen
    print("\n--- Simulation von 6 Runden ---")
    for round_num in range(1, 7):
        print(f"\n--- Runde {round_num} ---")
        for _ in range(game.state.cnt_player):  # Jeder Spieler macht einen Zug
            print(f"\nSpieler {game.state.idx_player_active + 1} ist am Zug.")
            available_actions = game.get_list_action()
            if available_actions:
                # Wähle zufällig eine Aktion aus
                selected_action = random.choice(available_actions)
                game.apply_action(selected_action)
                print(f"Aktion durchgeführt: {selected_action}")
            else:
                # Keine Aktionen verfügbar, Zug überspringen
                game.apply_action(None)
                print("Keine Aktionen verfügbar. Karten abgelegt.")

            # Debugging: Kartenverteilung überprüfen
            debug_card_distribution()

        # Überprüfe, ob das Spiel beendet ist
        game.check_game_status()
        if game.state.phase == GamePhase.FINISHED:
            print(f"Das Spiel ist beendet. Gewinner: Spieler {game.state.idx_player_active + 1}")
            break

    # Endzustand des Spiels ausgeben
    print("\n--- Endzustand des Spiels ---")
    final_state = game.get_state()
    print(final_state)
    assert final_state.phase in [GamePhase.RUNNING, GamePhase.FINISHED], \
        f"Fehler: Spielphase muss RUNNING oder FINISHED sein, aber ist {final_state.phase}"


    @pytest.mark.parametrize("card_rank,steps", [
        ('A', [1, 11]),  # ACE
        ('2', [2]),      # TWO
        ('3', [3]),      # THREE
        ('4', [4, -4]),  # FOUR
        ('5', [5]),      # FIVE
        ('6', [6]),      # SIX
        ('7', [1, 2, 3, 4, 5, 6, 7]),  # SEVEN
        ('8', [8]),      # EIGHT
        ('9', [9]),      # NINE
        ('10', [10]),    # TEN
        ('Q', [12]),     # QUEEN
        ('K', [13])      # KING
    ])
    def test_move_with_card_from_start(game, card_rank, steps):
        """Test moving with various cards from the start."""
        state = game.get_state()
        idx_player_active = state.idx_player_active
        player = state.list_player[idx_player_active]

        # Set up the card and marble positions
        card = Card(suit='♠', rank=card_rank)
        player.list_card = [card]
        player.list_marble[0].pos = None  # Marble in the kennel

        game.set_state(state)

        # Validate actions
        actions = game.get_list_action()
        expected_actions = [Action(card=card, pos_from=None, pos_to=step) for step in steps]

        assert len(actions) == len(expected_actions), f"Expected {len(expected_actions)} actions, found {len(actions)}"
        for action, expected in zip(actions, expected_actions):
            assert action.card == expected.card
            assert action.pos_from == expected.pos_from
            assert action.pos_to in steps

        # Apply the first action and validate state
        game.apply_action(actions[0])
        updated_state = game.get_state()
        assert updated_state.list_player[idx_player_active].list_marble[0].pos == actions[0].pos_to


