from functools import cache
from json import dump
from typing import cast

from tic_tac_toe import Board, new_board
from tic_tac_toe.tic_tac_toe import (
    Board,
    GameState,
    Marker,
    available_plays,
    game_state,
    is_game_over,
    next_marker_to_place,
    transition,
)


@cache
def serialize(board: Board) -> str:
    return "".join(str(c) for c in board)


@cache
def remap_to_ego(board: Board) -> str:
    return (
        serialize(board)
        if next_marker_to_place(board) == Marker.SECOND_PLAYER
        else "".join(
            "1" if c == "2" else ("2" if c == "1" else "0") for c in serialize(board)
        )
    )


@cache
def deserialize(state: str) -> Board:
    return cast(Board, tuple([int(c) for c in state]))


def terminal_value(board: Board, player: Marker):
    outcome: GameState = game_state(board)
    if outcome == GameState.FIRST_PLAYER_WON:
        return +1.0 if player == Marker.FIRST_PLAYER else -1.0
    if outcome == GameState.SECOND_PLAYER_WON:
        return -1.0 if player == Marker.FIRST_PLAYER else 1.0
    return 0.0


def minimax(board: Board, vtable: dict[str, float], player: Marker):
    key: str = serialize(board)
    if key in vtable:
        return vtable[key]
    if is_game_over(board):
        return vtable.setdefault(key, terminal_value(board, player))

    if next_marker_to_place(board) == player:
        # player to move → maximize
        best: float = float("-inf")
        for m in available_plays(board):
            val = minimax(transition(board, m), vtable, player)
            best = max(best, val)
    else:
        # opponent to move → minimize
        best: float = float("inf")
        for m in available_plays(board):
            val = minimax(transition(board, m), vtable, player)
            best = min(best, val)

    return vtable.setdefault(key, best)


def main():
    vtable1: dict[str, float] = {}
    minimax(new_board(), vtable1, Marker.FIRST_PLAYER)
    vtable2: dict[str, float] = {}
    minimax(new_board(), vtable2, Marker.SECOND_PLAYER)

    vtable: dict[str, float] = {}
    for state, val in vtable1.items():
        board = deserialize(state)
        if next_marker_to_place(board) == Marker.SECOND_PLAYER:
            vtable[remap_to_ego(board)] = val

    for state, val in vtable2.items():
        board = deserialize(state)
        if next_marker_to_place(board) == Marker.FIRST_PLAYER:
            vtable[remap_to_ego(board)] = val

    with open("vtable.json", "w") as f:
        dump(vtable, f)


if __name__ == "__main__":
    main()
