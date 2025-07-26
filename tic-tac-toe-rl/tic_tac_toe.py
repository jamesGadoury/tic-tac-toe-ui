import logging
from enum import Enum
from functools import cache
from typing import Self, cast

logger = logging.getLogger(__name__)


class Board:
    class Marker(Enum):
        EMPTY = 0
        FIRST_PLAYER = 1
        SECOND_PLAYER = 2

    State = tuple[
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

    def __init__(self):
        self._state = cast(Board.State, (Board.Marker.EMPTY,) * 9)

    @property
    def state(self) -> State:
        return self._state

    @property
    def next_marker_to_place(self) -> Marker:
        player_marker_count = len(self._state) - self._state.count(Board.Marker.EMPTY)
        logger.debug(f"{player_marker_count=}")
        return (
            Board.Marker.FIRST_PLAYER
            if player_marker_count % 2 == 0
            else Board.Marker.SECOND_PLAYER
        )

    @property
    def available_cell_indices(self) -> tuple[int, ...]:
        return tuple(idx for idx in range(len(self._state)) if not self.occupied(idx))

    def occupied(self, idx) -> bool:
        return self._state[idx] != Board.Marker.EMPTY

    def transition(self, idx: int) -> Self:
        if idx not in self.available_cell_indices:
            raise RuntimeError("illegal move")

        new_board = self.__class__()
        updated_state = list(self._state)
        updated_state[idx] = self.next_marker_to_place
        new_board._state = tuple(updated_state)

        logger.debug(
            f"""
transitioned from:
{self.pretty_format()}
transitioned to:
{new_board.pretty_format()}
        """
        )

        return new_board

    def pretty_format(self) -> str:
        """Output pretty format"""
        keys = {
            Board.Marker.EMPTY: "_",
            Board.Marker.FIRST_PLAYER: "X",
            Board.Marker.SECOND_PLAYER: "O",
        }

        s = ""
        for i in range(0, 9, 3):
            s += f"{keys[self._state[i]]} {keys[self._state[i+1]]} {keys[self._state[i+2]]}\n"
        return s


class GameState(Enum):
    INCOMPLETE = 0
    FIRST_PLAYER_WON = 1
    SECOND_PLAYER_WON = 2
    TIED = 3


def game_state(board: Board) -> GameState:
    if is_tied(board.state):
        return GameState.TIED
    if first_player_won(board.state):
        return GameState.FIRST_PLAYER_WON
    if second_player_won(board.state):
        return GameState.SECOND_PLAYER_WON
    return GameState.INCOMPLETE


@cache
def is_tied(board_state: Board.State) -> bool:
    return all([marker != Board.Marker.EMPTY for marker in board_state])


@cache
def first_player_won(board_state: Board.State) -> bool:
    winning_player_marker = _find_winning_player_marker(board_state)
    logger.debug(f"{winning_player_marker=}")
    if winning_player_marker is None:
        return False
    return winning_player_marker == Board.Marker.FIRST_PLAYER


@cache
def second_player_won(board_state: Board.State) -> bool:
    winning_player_marker = _find_winning_player_marker(board_state)
    logger.debug(f"{winning_player_marker=}")
    if winning_player_marker is None:
        return False
    return winning_player_marker == Board.Marker.SECOND_PLAYER


_WINNING_GAME_COMBOS = (
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
def _find_winning_player_marker(board_state: Board.State) -> Board.Marker | None:
    for combo in _WINNING_GAME_COMBOS:
        line = tuple(board_state[idx] for idx in combo)

        logger.debug(f"{combo=}")
        logger.debug(f"{line=}")

        if len(set(line)) == 1 and line[0] != Board.Marker.EMPTY:
            return line[0]

    return None
