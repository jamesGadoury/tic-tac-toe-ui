import pytest
from egocentric import (
    FLIP_ACTION,
    ROT90_ACTION,
    EgocentricMarker,
    canonicalize_board_action,
    flip,
    remap_to_egocentric_board,
    rotate90,
)
from tic_tac_toe import Marker, new_board, next_marker_to_place, transition

# ------------------ remap_to_egocentric_board tests ------------------


def test_remap_empty_board_all_empty():
    b = new_board()
    e = remap_to_egocentric_board(b)
    assert isinstance(e, tuple)
    assert len(e) == 9
    assert all(cell is EgocentricMarker.EMPTY for cell in e)


def test_remap_after_one_move_marks_opponent():
    b0 = new_board()
    b1 = transition(b0, 3)
    assert next_marker_to_place(b1) is Marker.SECOND_PLAYER
    e = remap_to_egocentric_board(b1)
    assert e[3] is EgocentricMarker.OPPONENT
    for i, cell in enumerate(e):
        if i != 3:
            assert cell is EgocentricMarker.EMPTY


def test_remap_after_two_moves_alternates_agent_opponent():
    b = new_board()
    b = transition(b, 0)
    b = transition(b, 1)
    assert next_marker_to_place(b) is Marker.FIRST_PLAYER
    e = remap_to_egocentric_board(b)
    assert e[0] is EgocentricMarker.AGENT
    assert e[1] is EgocentricMarker.OPPONENT
    for i, cell in enumerate(e):
        if i not in (0, 1):
            assert cell is EgocentricMarker.EMPTY


def test_remap_cache_returns_same_object():
    b = new_board()
    b = transition(b, 4)
    e1 = remap_to_egocentric_board(b)
    e2 = remap_to_egocentric_board(b)
    assert e1 is e2


# -------------- symmetry mapping tests --------------


def test_rotate90_mapping_consistency():
    for idx in range(9):
        one = [0] * 9
        one[idx] = 1
        rotated = rotate90(tuple(one))
        new_idx = rotated.index(1)
        assert ROT90_ACTION[idx] == new_idx


def test_flip_mapping_consistency():
    for idx in range(9):
        one = [0] * 9
        one[idx] = 1
        flipped = flip(tuple(one))
        new_idx = flipped.index(1)
        assert FLIP_ACTION[idx] == new_idx


# -------------- canonicalize_board_action tests --------------


@pytest.fixture
def sample_board_action():
    board = [0] * 9
    board[2] = 1
    board[5] = 2
    action = 7
    return tuple(board), action


def all_sym_board_actions(board, action):
    forms = []
    b_rot, a_rot = board, action
    for _ in range(4):
        forms.append((b_rot, a_rot))
        b_flip = flip(b_rot)
        a_flip = FLIP_ACTION[a_rot]
        forms.append((b_flip, a_flip))
        b_rot = rotate90(b_rot)
        a_rot = ROT90_ACTION[a_rot]
    return forms


def test_canonicalize_board_action_idempotent_and_cached(sample_board_action):
    board, action = sample_board_action
    c1 = canonicalize_board_action(board, action)
    c2 = canonicalize_board_action(board, action)
    assert c1 == c2
    assert c1 is c2


def test_canonicalize_board_action_lexico_minimum(sample_board_action):
    board, action = sample_board_action
    forms = all_sym_board_actions(board, action)
    expected = min(forms)
    got = canonicalize_board_action(board, action)
    assert got == expected


def test_canonicalize_invariant_under_symmetries(sample_board_action):
    board, action = sample_board_action
    base = canonicalize_board_action(board, action)
    for b_test, a_test in all_sym_board_actions(board, action):
        assert canonicalize_board_action(b_test, a_test) == base


def test_canonicalize_on_empty_board_any_action():
    board = tuple(0 for _ in range(9))
    for action in range(9):
        canon_b, canon_a = canonicalize_board_action(board, action)
        # Board stays the same
        assert canon_b == board
        # Action should be the minimum over its symmetry orbit
        orbit = []
        a_rot = action
        for _ in range(4):
            orbit.append(a_rot)
            orbit.append(FLIP_ACTION[a_rot])
            a_rot = ROT90_ACTION[a_rot]
        assert canon_a == min(orbit)
