import logging
from typing import Self

import numpy as np

# place this at module top
logger = logging.getLogger(__name__)


class TicTacToeBoard:
    EMPTY_CELL, FIRST_PLAYER_CELL, SECOND_PLAYER_CELL = 0, 1, 2

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

    WIN_ARRAY = np.array(WIN_COMBOS, dtype=int)  # shape (8,3)

    def __init__(self):
        # NOTE: using EMPTY in case that value changes
        #       for whatever reason, but obv if EMPTY=0
        #       then this is equivalent to np.zeros((9,))
        self._state = np.ones((9,)) * TicTacToeBoard.EMPTY_CELL

    @property
    def state(self) -> tuple[int, ...]:
        return tuple(self._state.tolist())

    def player_to_move(self) -> int:
        return (
            TicTacToeBoard.FIRST_PLAYER_CELL
            if len(self.available_cell_indices()) % 2 == 1
            else TicTacToeBoard.SECOND_PLAYER_CELL
        )

    def available_cell_indices(self) -> tuple[int, ...]:
        return tuple((self._state == TicTacToeBoard.EMPTY_CELL).nonzero()[0].tolist())

    def terminated(self) -> bool:
        return self.tied() or self.first_player_won() or self.second_player_won()

    def tied(self) -> bool:
        return (self._state != TicTacToeBoard.EMPTY_CELL).all()

    def first_player_won(self) -> bool:
        return self.player_won(player=TicTacToeBoard.FIRST_PLAYER_CELL)

    def second_player_won(self) -> bool:
        return self.player_won(player=TicTacToeBoard.SECOND_PLAYER_CELL)

    def player_won(self, player: int) -> bool:
        cells = self._state[TicTacToeBoard.WIN_ARRAY]
        return bool(np.any(np.all(cells == player, axis=1)))

    def transition(self, idx: int) -> Self:
        if self.terminated():
            raise RuntimeError("move attempted on completed game")

        if idx not in self.available_cell_indices():
            raise RuntimeError("illegal move")
        new_board = self.__class__()
        new_board._state = self._state.copy()
        new_board._state[idx] = self.player_to_move()
        return new_board

    def debug_display(self) -> None:
        """Log the board layout (ignored if logging level is set to DEBUG."""
        keys = {
            TicTacToeBoard.FIRST_PLAYER_CELL: "X",
            TicTacToeBoard.SECOND_PLAYER_CELL: "O",
            TicTacToeBoard.EMPTY_CELL: "_",
        }

        lines = []
        for i in range(0, 9, 3):
            lines.append(
                f"{keys[self._state[i]]} "
                f"{keys[self._state[i+1]]} "
                f"{keys[self._state[i+2]]}"
            )

        for row in lines:
            logger.log(logging.DEBUG, row)
        # add a blank line for spacing
        logger.log(logging.DEBUG, "")
