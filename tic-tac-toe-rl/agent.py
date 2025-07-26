from enum import IntEnum
from functools import cache
from typing import cast

from tic_tac_toe import Board, Marker, next_marker_to_place


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
def remap_to_egocentric_board(board: Board) -> EgocentricBoard:
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
    next_marker = next_marker_to_place(board)
    return cast(
        EgocentricBoard,
        tuple(
            (
                EgocentricMarker.EMPTY
                if m == Marker.EMPTY
                else (
                    EgocentricMarker.AGENT
                    if m == next_marker
                    else EgocentricMarker.OPPONENT
                )
            )
            for m in board
        ),
    )


@cache
def canonicalize(board: EgocentricBoard) -> EgocentricBoard:
    """Transforms board into a "canonical" version that treats symmetrical boards as same state.

    Returns a “canonical” version of the board by considering all
    8 symmetries (4 rotations × optional flip) and picking the
    lexicographically smallest tuple.
    """

    def rotate90(s: EgocentricBoard) -> EgocentricBoard:
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

    # helper to flip horizontally
    def flip(s: EgocentricBoard) -> EgocentricBoard:
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

    forms = []
    s = board
    for _ in range(4):
        forms.append(s)
        forms.append(flip(s))
        s = rotate90(s)

    return min(forms)  # lexicographically smallest
