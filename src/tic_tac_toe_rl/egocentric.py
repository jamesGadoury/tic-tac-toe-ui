import logging
from enum import IntEnum
from functools import cache
from typing import cast

from .tic_tac_toe import Board, Marker

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
def remap_to_egocentric_board(board: Board, agent_marker: Marker) -> EgocentricBoard:
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
                    EgocentricMarker.AGENT
                    if m == agent_marker
                    else EgocentricMarker.OPPONENT
                )
            )
            for m in board
        ),
    )
