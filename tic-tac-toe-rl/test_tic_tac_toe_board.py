import numpy as np
import pytest
from tic_tac_toe_board import TicTacToeBoard


def test_initial_state_and_properties():
    board = TicTacToeBoard()
    # initial state should be all EMPTY_CELL
    assert board.state == (TicTacToeBoard.EMPTY_CELL,) * 9
    # all cells available
    assert board.available_cell_indices() == tuple(range(9))
    # first player moves first (9 available ⇒ odd)
    assert board.player_to_move() == TicTacToeBoard.FIRST_PLAYER_CELL
    # no one has won, not tied, not terminated
    assert not board.first_player_won()
    assert not board.second_player_won()
    assert not board.tied()
    assert not board.terminated()


def test_transition_and_illegal_moves():
    board = TicTacToeBoard()
    # out‑of‑range index
    with pytest.raises(RuntimeError):
        board.transition(9)
    # legal move
    b1 = board.transition(0)
    assert board.state[0] == TicTacToeBoard.EMPTY_CELL  # original unmodified
    assert b1.state[0] == TicTacToeBoard.FIRST_PLAYER_CELL
    # cannot move again on the same cell
    with pytest.raises(RuntimeError):
        b1.transition(0)


def test_win_detection_and_termination():
    # first‑player horizontal win on top row
    moves = [0, 3, 1, 4, 2]  # X at 0,1,2; O at 3,4
    board = TicTacToeBoard()
    for idx in moves:
        board = board.transition(idx)
    assert board.first_player_won()
    assert not board.second_player_won()
    assert board.terminated()
    # no further moves allowed
    with pytest.raises(RuntimeError):
        board.transition(5)

    # second‑player diagonal win (0,4,8)
    seq = [1, 0, 2, 4, 3, 8]  # X at 1,2,3; O at 0,4,8
    board = TicTacToeBoard()
    for idx in seq:
        board = board.transition(idx)
    assert board.second_player_won()
    assert board.terminated()


def test_tie_detection():
    # Fill board with no winner
    tie_moves = [0, 1, 2, 4, 3, 5, 7, 6, 8]
    board = TicTacToeBoard()
    for idx in tie_moves:
        board = board.transition(idx)
    assert board.tied()
    assert board.terminated()
    assert not board.first_player_won()
    assert not board.second_player_won()
