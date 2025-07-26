import logging

import pytest
from tic_tac_toe import Board

Marker = Board.Marker


def test_initial_state_and_properties():
    board = Board()
    # state must be a 9‐tuple of EMPTY
    assert isinstance(board.state, tuple)
    assert len(board.state) == 9
    assert all(cell is Marker.EMPTY for cell in board.state)
    # no one has moved, so FIRST_PLAYER goes next
    assert board.next_marker_to_place is Marker.FIRST_PLAYER
    # all cells available initially
    assert board.available_cell_indices == tuple(range(9))


def test_occupied_and_available_cell_indices():
    board = Board()
    # no cell is occupied at start
    for i in range(9):
        assert board.occupied(i) is False
    # out‐of‐range raises IndexError
    with pytest.raises(IndexError):
        board.occupied(9)

    # after a move at 4, that cell must be occupied
    b2 = board.transition(4)
    assert board.occupied(4) is False  # original unchanged
    assert b2.occupied(4) is True
    # available_cell_indices must shrink by one
    assert 4 not in b2.available_cell_indices
    assert len(b2.available_cell_indices) == 8


def test_transition_immutability_and_alternation():
    board = Board()
    # first move -> index 2
    b1 = board.transition(2)
    assert b1.state[2] is Marker.FIRST_PLAYER
    assert board.state[2] is Marker.EMPTY  # original untouched
    # now it's second player's turn
    assert b1.next_marker_to_place is Marker.SECOND_PLAYER

    # second move -> index 5
    b2 = b1.transition(5)
    assert b2.state[5] is Marker.SECOND_PLAYER
    # back to first player's turn
    assert b2.next_marker_to_place is Marker.FIRST_PLAYER

    # older boards remain unchanged
    assert board.state.count(Marker.EMPTY) == 9
    assert b1.state[5] is Marker.EMPTY


def test_transition_illegal_and_edge_indices():
    board = Board()
    b1 = board.transition(0)
    # cannot move again on 0
    with pytest.raises(RuntimeError) as ei:
        b1.transition(0)
    assert "illegal move" in str(ei.value)

    # non‐int also illegal
    with pytest.raises(RuntimeError):
        board.transition("foo")  # type: ignore

    # negative index not available
    with pytest.raises(RuntimeError):
        board.transition(-1)


def test_sequence_exhausts_and_errors_on_full():
    board = Board()
    b = board
    for i in range(9):
        assert i in b.available_cell_indices or -1 in b.available_cell_indices
        # always legal until full
        b = b.transition(i)
    # now no available cells
    assert b.available_cell_indices == ()
    # any further transition is illegal
    with pytest.raises(RuntimeError):
        b.transition(0)


def test_state_property_is_tuple_and_readonly():
    board = Board()
    st = board.state
    assert isinstance(st, tuple)
    with pytest.raises(TypeError):
        # cannot assign to a tuple element
        st[0] = Marker.FIRST_PLAYER  # type: ignore


def test_available_cell_indices_order_and_type():
    board = Board()
    # after moves [3,7,0], the available must be all others in ascending order
    b = board.transition(3).transition(7).transition(0)
    expected = tuple(i for i in range(9) if i not in {3, 7, 0})
    assert b.available_cell_indices == expected


def test_transition_returns_new_instance():
    board = Board()
    b1 = board.transition(4)
    assert isinstance(b1, Board)
    assert b1 is not board
    # further transitions chain
    b2 = b1.transition(5)
    assert isinstance(b2, Board)
    assert b2 is not b1
