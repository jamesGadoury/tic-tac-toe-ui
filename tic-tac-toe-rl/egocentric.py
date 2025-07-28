import logging
from enum import IntEnum
from functools import cache
from typing import cast

from tic_tac_toe import Board, Marker, next_marker_to_place

logger = logging.getLogger(__name__)


class EgocentricMarker(IntEnum):
    EMPTY = 0
    AGENT = 1
    OPPONENT = 2


EgocentricBoard = tuple[
    EgocentricMarker,
    EgocentricMarker,
    EgocentricMarker,
    EgocentricMarker,
    EgocentricMarker,
    EgocentricMarker,
    EgocentricMarker,
    EgocentricMarker,
    EgocentricMarker,
]


@cache
def remap_to_egocentric_board(board: Board, marker: Marker) -> EgocentricBoard:
    """Transforms the board to agent's perspective.

    This is helpful if you want the agent to play both/either
    first and/or second player. For sake of this
    code the board is remapped to the agent's perspective.

    If the same agent is playing both players (self-play) then
    the board will be remapped based on which marker is next
    to play. e.g. when it is the first player's turn, the
    agent will see itself on the board as first player and
    its opponent as second player. Likewise, when it is the
    second player's turn, the agent will see itself on
    the board as second player and its opponent as first player.

    Note that for tabular methods, this isn't necessary
    for learning as the first and second player will never
    "see" states that the other player sees, but in the off chance
    that you want to implement something that might
    infer relationships between elements in the state
    this could be helpful.

    Mainly this is done for consistency when running a policy
    developed in this environment outside of this environment.
    """
    return cast(
        EgocentricBoard,
        tuple(
            (
                EgocentricMarker.EMPTY
                if m == Marker.EMPTY
                else (
                    EgocentricMarker.AGENT if m == marker else EgocentricMarker.OPPONENT
                )
            )
            for m in board
        ),
    )


def rotate90(s: tuple[int, ...]) -> tuple[int, ...]:
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


def flip(s: tuple[int, ...]) -> tuple[int, ...]:
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


# 1) Build the action‐index maps by “spot‐and‐track”:
def make_index_map(transform):
    M = {}
    for old in range(9):
        # make a “one‐hot” board with a marker at `old`
        one = [0] * 9
        one[old] = 1
        new = transform(tuple(one))
        # find where that 1 ended up
        new_idx = new.index(1)
        M[old] = new_idx
    return M


ROT90_ACTION = make_index_map(rotate90)  # e.g. {0:2, 1:5, 2:8, …}
FLIP_ACTION = make_index_map(flip)  # e.g. {0:2, 1:1, 2:0, …}


@cache
def canonicalize_board_action(
    board: tuple[int, ...], action: int
) -> tuple[tuple[int, ...], int]:
    best: tuple[tuple[int, ...], int] | None = (
        None  # will hold (canon_board, canon_action)
    )
    # try all 4 rotations
    b_rot, a_rot = board, action
    for _ in range(4):
        # also try the flipped version
        b_flip = flip(b_rot)
        a_flip = FLIP_ACTION[a_rot]
        for b_candidate, a_candidate in ((b_rot, a_rot), (b_flip, a_flip)):
            pair = (b_candidate, a_candidate)
            if best is None or pair < best:
                best = pair
        # rotate for next iteration
        b_rot, a_rot = rotate90(b_rot), ROT90_ACTION[a_rot]

    assert best is not None
    return best  # (canonical_board, canonical_action)
