import logging

import pytest
from tic_tac_toe import (
    _WINNING_GAME_COMBOS,
    Board,
    GameState,
    Marker,
    available_plays,
    first_player_won,
    game_state,
    is_tied,
    new_board,
    next_marker_to_place,
    occupied,
    second_player_won,
    transition,
)

logger = logging.getLogger(__name__)


def test_initial_state_and_properties():
    board = new_board()
    # state must be a 9‐tuple of EMPTY
    assert isinstance(board, tuple)
    assert len(board) == 9
    assert all(cell is Marker.EMPTY for cell in board)
    # no one has moved, so FIRST_PLAYER goes next
    assert next_marker_to_place(board) is Marker.FIRST_PLAYER
    # all cells available initially
    assert available_plays(board) == tuple(range(9))


def test_occupied_and_available_plays():
    board = new_board()
    # no cell is occupied at start
    for i in range(9):
        assert occupied(board, i) is False
    # out‐of‐range raises IndexError
    with pytest.raises(IndexError):
        occupied(board, 9)

    # after a move at 4, that cell must be occupied
    b2 = transition(board, 4)
    assert occupied(board, 4) is False  # original unchanged
    assert occupied(b2, 4) is True
    # available_plays must shrink by one
    assert 4 not in available_plays(b2)
    assert len(available_plays(b2)) == 8


def test_transition_immutability_and_alternation():
    board = new_board()
    # first move -> index 2
    b1 = transition(board, 2)
    assert b1[2] is Marker.FIRST_PLAYER
    assert board[2] is Marker.EMPTY  # original untouched
    # now it's second player's turn
    assert next_marker_to_place(b1) is Marker.SECOND_PLAYER

    # second move -> index 5
    b2 = transition(b1, 5)
    assert b2[5] is Marker.SECOND_PLAYER
    # back to first player's turn
    assert next_marker_to_place(b2) is Marker.FIRST_PLAYER

    # older boards remain unchanged
    assert board.count(Marker.EMPTY) == 9
    assert b1[5] is Marker.EMPTY


def test_transition_illegal_and_edge_indices():
    board = new_board()
    b1 = transition(board, 0)
    # cannot move again on 0
    with pytest.raises(RuntimeError) as ei:
        b1 = transition(b1, 0)
    assert "illegal move" in str(ei.value)

    # non‐int also illegal
    with pytest.raises(RuntimeError):
        transition(board, "foo")  # type: ignore

    # negative index not available
    with pytest.raises(RuntimeError):
        transition(board, -1)


def test_sequence_exhausts_and_errors_on_full():
    b = new_board()
    for i in range(9):
        assert i in available_plays(b) or -1 in available_plays(b)
        # always legal until full
        b = transition(b, i)
    # now no available cells
    assert available_plays(b) == ()
    # any further transition is illegal
    with pytest.raises(RuntimeError):
        b = transition(b, 0)


def test_state_property_is_tuple_and_readonly():
    board = new_board()
    st = board
    assert isinstance(st, tuple)
    with pytest.raises(TypeError):
        # cannot assign to a tuple element
        st[0] = Marker.FIRST_PLAYER  # type: ignore


def test_available_plays_order_and_type():
    b = new_board()
    # after moves [3,7,0], the available must be all others in ascending order
    for i in (
        3,
        7,
        0,
    ):
        b = transition(b, i)
    expected = tuple(i for i in range(9) if i not in {3, 7, 0})
    assert available_plays(b) == expected


def test_transition_returns_new_instance():
    board = new_board()
    b1 = transition(board, 4)
    assert b1 is not board


def test_incomplete_on_new_board():
    b = new_board()
    st = b
    assert not is_tied(st)
    assert not first_player_won(st)
    assert not second_player_won(st)
    assert game_state(b) == GameState.INCOMPLETE


def test_tied_board_detection():
    # fill without any win: [0,1,2,4,3,5,7,6,8]
    b = new_board()
    for idx in [0, 1, 2, 4, 3, 5, 7, 6, 8]:
        b = transition(b, idx)
    st = b
    assert is_tied(st)
    assert not first_player_won(st)
    assert not second_player_won(st)
    assert game_state(b) == GameState.TIED


@pytest.mark.parametrize("combo", _WINNING_GAME_COMBOS)
def test_first_player_win_via_game_state(combo):
    # Plan moves so FIRST_PLAYER plays at positions 0,2,4 in seq:
    free = [i for i in range(9) if i not in combo]
    seq = [combo[0], free[0], combo[1], free[1], combo[2]]
    logger.debug(f"{seq=}")

    b = new_board()
    for idx in seq:
        b = transition(b, idx)

    st = b
    assert first_player_won(st)
    assert not second_player_won(st)
    assert not is_tied(st)
    assert game_state(b) == GameState.FIRST_PLAYER_WON


@pytest.mark.parametrize("combo", _WINNING_GAME_COMBOS)
def test_second_player_win_via_game_state(combo):
    # Plan moves so SECOND_PLAYER plays at positions 1,3,5 in seq:
    #   [F1, combo[0], F2, combo[1], F3, combo[2]]
    free = [i for i in range(9) if i not in combo]
    F1, F2, F3 = free[0], free[1], free[2]
    if (
        F1,
        F2,
        F3,
    ) in _WINNING_GAME_COMBOS:
        F3 = free[3]

    seq = [F1, combo[0], F2, combo[1], F3, combo[2]]

    b = new_board()
    for idx in seq:
        b = transition(b, idx)

    st = b
    assert second_player_won(st)
    assert not first_player_won(st)
    assert not is_tied(st)
    assert game_state(b) == GameState.SECOND_PLAYER_WON


def test_mixed_states_do_not_falsely_report_win_or_tie():
    # Partial fill, no winner yet
    b = new_board()
    for i in (
        0,
        3,
        1,
    ):
        b = transition(b, i)
    st = b
    assert not is_tied(st)
    assert not first_player_won(st)
    assert not second_player_won(st)
    assert game_state(b) == GameState.INCOMPLETE

    # Three in a row but interrupted by opposite marker
    # e.g. [0]=X, [1]=O, [2]=X → no winner
    b2 = new_board()
    for i in (
        0,
        1,
        2,
    ):
        b2 = transition(b2, i)
    st2 = b2
    assert not first_player_won(st2)
    assert not second_player_won(st2)
    assert game_state(b2) == GameState.INCOMPLETE
