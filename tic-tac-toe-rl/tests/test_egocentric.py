import pytest
from egocentric import EgocentricMarker, canonicalize, remap_to_egocentric_board
from tic_tac_toe import Marker, new_board, next_marker_to_place, transition


def test_remap_empty_board_all_empty():
    b = new_board()
    e = remap_to_egocentric_board(b)
    # should be a 9‐tuple of EMPTY
    assert isinstance(e, tuple)
    assert len(e) == 9
    assert all(cell is EgocentricMarker.EMPTY for cell in e)


def test_remap_after_one_move_marks_opponent():
    # first move is FIRST_PLAYER; next_marker is SECOND_PLAYER,
    # so existing FIRST_PLAYER marks map to OPPONENT
    b0 = new_board()
    b1 = transition(b0, 3)
    assert next_marker_to_place(b1) is Marker.SECOND_PLAYER
    e = remap_to_egocentric_board(b1)
    # index 3 was X → now OPPONENT
    assert e[3] is EgocentricMarker.OPPONENT
    # all other cells remain EMPTY
    for i in range(9):
        if i != 3:
            assert e[i] is EgocentricMarker.EMPTY


def test_remap_after_two_moves_alternates_agent_opponent():
    # X at 0, O at 1 → next_marker is FIRST_PLAYER
    b = new_board()
    b = transition(b, 0)
    b = transition(b, 1)
    assert next_marker_to_place(b) is Marker.FIRST_PLAYER
    e = remap_to_egocentric_board(b)
    # X cells (Marker.FIRST_PLAYER) become AGENT
    assert e[0] is EgocentricMarker.AGENT
    # O cells (Marker.SECOND_PLAYER) become OPPONENT
    assert e[1] is EgocentricMarker.OPPONENT
    # rest are EMPTY
    for i in range(9):
        if i not in (0, 1):
            assert e[i] is EgocentricMarker.EMPTY


def test_remap_cache_returns_same_object():
    b = new_board()
    b = transition(b, 4)
    e1 = remap_to_egocentric_board(b)
    e2 = remap_to_egocentric_board(b)
    # @cache means the same tuple object is returned
    assert e1 is e2


@pytest.fixture
def sample_egocentric_board():
    # create a non‐trivial egocentric board:
    # AGENT at 2, OPPONENT at 5, rest EMPTY
    eb = [EgocentricMarker.EMPTY] * 9
    eb[2] = EgocentricMarker.AGENT
    eb[5] = EgocentricMarker.OPPONENT
    return tuple(eb)


def rotate90(s):
    return (
        s[6],
        s[3],
        s[0],
        s[7],
        s[4],
        s[1],
        s[8],
        s[5],
        s[2],
    )


def flip(s):
    return (
        s[2],
        s[1],
        s[0],
        s[5],
        s[4],
        s[3],
        s[8],
        s[7],
        s[6],
    )


def all_symmetries(s):
    forms = []
    cur = s
    for _ in range(4):
        forms.append(cur)
        forms.append(flip(cur))
        cur = rotate90(cur)
    return forms


def test_canonicalize_idempotent_and_cached(sample_egocentric_board):
    eb = sample_egocentric_board
    c1 = canonicalize(eb)
    c2 = canonicalize(eb)
    # idempotent and cached: same object
    assert c1 == c2
    assert c1 is c2


def test_canonicalize_chooses_lexicographic_minimum(sample_egocentric_board):
    eb = sample_egocentric_board
    forms = all_symmetries(eb)
    expected = min(forms)
    got = canonicalize(eb)
    assert got == expected


def test_canonicalize_invariant_under_rotations_and_flips(sample_egocentric_board):
    eb = sample_egocentric_board
    base = canonicalize(eb)
    for form in all_symmetries(eb):
        assert canonicalize(form) == base


def test_canonicalize_on_all_empty_board():
    eb = tuple(EgocentricMarker.EMPTY for _ in range(9))
    c = canonicalize(eb)
    # all symmetries are identical, so canonical is just all‐empty
    assert c == eb


def test_canonicalize_on_full_agent_board():
    eb = tuple(EgocentricMarker.AGENT for _ in range(9))
    c = canonicalize(eb)
    # no variation across symmetries
    assert c == eb
