import logging
from enum import Enum
from typing import Self, cast

logger = logging.getLogger(__name__)


class TicTacToeBoard:
    WIN_COMBOS = (
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),
        (0, 4, 8),
        (2, 4, 6),
    )

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
        self._state = cast(TicTacToeBoard.State, (TicTacToeBoard.Marker.EMPTY,) * 9)

    @property
    def state(self) -> State:
        return self._state

    @property
    def next_marker_to_place(self) -> Marker:
        player_marker_count = len(self._state) - self._state.count(
            TicTacToeBoard.Marker.EMPTY
        )
        logger.debug(f"{player_marker_count=}")
        return (
            TicTacToeBoard.Marker.FIRST_PLAYER
            if player_marker_count % 2 == 0
            else TicTacToeBoard.Marker.SECOND_PLAYER
        )

    @property
    def available_cell_indices(self) -> tuple[int, ...]:
        return tuple(idx for idx in range(len(self._state)) if not self.occupied(idx))

    def occupied(self, idx) -> bool:
        return self._state[idx] != TicTacToeBoard.Marker.EMPTY

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
            TicTacToeBoard.Marker.EMPTY: "_",
            TicTacToeBoard.Marker.FIRST_PLAYER: "X",
            TicTacToeBoard.Marker.SECOND_PLAYER: "O",
        }

        s = ""
        for i in range(0, 9, 3):
            s += f"{keys[self._state[i]]} {keys[self._state[i+1]]} {keys[self._state[i+2]]}\n"
        return s
