from argparse import ArgumentParser
from collections import defaultdict
from itertools import cycle
from json import load
from pathlib import Path
from random import choice
from typing import Protocol

from generate_vtable_minimax import remap_to_ego
from tqdm import tqdm

from tic_tac_toe.tic_tac_toe import (
    Board,
    GameState,
    available_plays,
    game_state,
    is_game_over,
    new_board,
    transition,
)

FIRST, SECOND = 1, 2


class Agent(Protocol):
    def get_action(self, board: Board) -> int: ...


class ValueAgent(Agent):
    def __init__(self, vtable: dict[str, float]):
        self.vtable: dict[str, float] = vtable

    def get_action(self, board: Board) -> int:
        plays = available_plays(board)
        values: list[tuple[float, int]] = []
        for play in plays:
            child = transition(board, play)
            values.append(
                (
                    self.vtable[remap_to_ego(child)],
                    play,
                )
            )
        return max(values, key=lambda t: t[0])[1]


class RandomAgent(Agent):
    def get_action(self, board: Board) -> int:
        return choice(available_plays(board))


def play_game(vtable: dict[str, float], agent_playing: int) -> GameState:
    assert agent_playing in [FIRST, SECOND]
    board: Board = new_board()
    player: cycle[Agent] = (
        cycle([ValueAgent(vtable=vtable), RandomAgent()])
        if agent_playing == FIRST
        else cycle([RandomAgent(), ValueAgent(vtable=vtable)])
    )

    while True:
        action: int = next(player).get_action(board=board)
        board: Board = transition(board=board, idx=action)
        if is_game_over(board=board):
            return game_state(board=board)


def main(vtable: dict[str, float], num_games: int, agent_playing: int):
    assert agent_playing in [FIRST, SECOND]
    outcomes: dict[GameState, int] = defaultdict(int)
    for _ in tqdm(range(num_games)):
        outcomes[play_game(vtable=vtable, agent_playing=agent_playing)] += 1

    print(outcomes)


if __name__ == "__main__":
    cli = ArgumentParser()
    cli.add_argument("--vtable-path", type=Path, default=Path("./vtable.json"))
    cli.add_argument("--num-games", type=int, default=1000000)
    cli.add_argument(
        "--agent-playing", type=int, choices=[FIRST, SECOND], default=FIRST
    )
    args = cli.parse_args()
    main(
        vtable=load(open(args.vtable_path, "r")),
        num_games=args.num_games,
        agent_playing=args.agent_playing,
    )
