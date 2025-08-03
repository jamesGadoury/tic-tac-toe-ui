import logging
from enum import IntEnum
from functools import cache
from typing import cast

logger = logging.getLogger(__name__)


class Marker(IntEnum):
    EMPTY = 0
    FIRST_PLAYER = 1
    SECOND_PLAYER = 2


Board = tuple[
    Marker,
    Marker,
    Marker,
    Marker,
    Marker,
    Marker,
    Marker,
    Marker,
    Marker,
]


def new_board() -> Board:
    return cast(Board, (Marker.EMPTY,) * 9)


@cache
def next_marker_to_place(board: Board) -> Marker:
    player_marker_count = len(board) - board.count(Marker.EMPTY)
    return Marker.FIRST_PLAYER if player_marker_count % 2 == 0 else Marker.SECOND_PLAYER


@cache
def occupied(board: Board, idx: int) -> bool:
    return board[idx] != Marker.EMPTY


@cache
def available_plays(board: Board) -> tuple[int, ...]:
    return tuple(idx for idx in range(len(board)) if not occupied(board, idx))


@cache
def transition(board: Board, idx: int) -> Board:
    if idx not in available_plays(board):
        raise RuntimeError("illegal move")

    updated_board = list(board)
    updated_board[idx] = next_marker_to_place(board)
    updated_board = cast(Board, tuple(updated_board))

    logger.debug(
        f"""
transitioned from:
{pretty_format(board)}
transitioned to:
{pretty_format(updated_board)}
"""
    )

    return updated_board


@cache
def pretty_format(board: Board) -> str:
    """Output pretty format"""
    keys = {
        Marker.EMPTY: "_",
        Marker.FIRST_PLAYER: "X",
        Marker.SECOND_PLAYER: "O",
    }

    s = ""
    for i in range(0, 9, 3):
        s += f"{keys[board[i]]} {keys[board[i+1]]} {keys[board[i+2]]}\n"
    return s


class GameState(IntEnum):
    INCOMPLETE = 0
    FIRST_PLAYER_WON = 1
    SECOND_PLAYER_WON = 2
    TIED = 3


@cache
def game_state(board: Board) -> GameState:
    if first_player_won(board):
        logger.debug("first_player_won")
        return GameState.FIRST_PLAYER_WON
    if second_player_won(board):
        logger.debug("second_player_won")
        return GameState.SECOND_PLAYER_WON
    if is_tied(board):
        logger.debug("is_tied")
        return GameState.TIED
    return GameState.INCOMPLETE


@cache
def is_game_over(board: Board) -> bool:
    return game_state(board) != GameState.INCOMPLETE


@cache
def is_tied(board: Board) -> bool:
    return all([marker != Marker.EMPTY for marker in board])


@cache
def first_player_won(board: Board) -> bool:
    winning_player_marker = _find_winning_player_marker(board)
    if winning_player_marker is None:
        return False
    return winning_player_marker == Marker.FIRST_PLAYER


@cache
def second_player_won(board: Board) -> bool:
    winning_player_marker = _find_winning_player_marker(board)
    logger.debug(f"{winning_player_marker=}")
    if winning_player_marker is None:
        return False
    return winning_player_marker == Marker.SECOND_PLAYER


WINNING_GAME_COMBOS = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


@cache
def _find_winning_player_marker(board: Board) -> Marker | None:
    for combo in WINNING_GAME_COMBOS:
        line = tuple(board[idx] for idx in combo)

        if len(set(line)) == 1 and line[0] != Marker.EMPTY:
            return line[0]

    return None
