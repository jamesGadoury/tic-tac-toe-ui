import json
from argparse import ArgumentParser
from dataclasses import asdict, dataclass
from enum import IntEnum
from math import exp
from pathlib import Path
from random import choice, seed
from time import time_ns
from typing import Any, Protocol

from agents import Agent, QAgent, RandomAgent
from tic_tac_toe import (
    Board,
    GameState,
    Marker,
    available_plays,
    game_state,
    new_board,
    next_marker_to_place,
    transition,
)
from tqdm import tqdm
from train import find_most_recent_file_with_substring, reward_from_board_transition


def load_q_agent(dir: Path, marker: Marker) -> QAgent:
    # NOTE: very hacky, have to search for canonical first because q_table will match both canonical and regular q tables
    canonical_q_table_pth = find_most_recent_file_with_substring(
        dir=Path(dir), substring="canonical_q_table"
    )
    assert canonical_q_table_pth is not None
    q_table_pth = canonical_q_table_pth.with_name(
        canonical_q_table_pth.name.replace("canonical_", "")
    )

    canonical_q_table = json.load(open(canonical_q_table_pth, "r"))
    q_table = json.load(open(q_table_pth, "r"))

    print(f"Loaded {canonical_q_table_pth}")
    print(f"Loaded {q_table_pth}")

    return QAgent.load(
        canonical_q_table=canonical_q_table,
        q_table=q_table,
        marker=marker,
        frozen=False,
    )


def eval(n_episodes: int, agents: dict[Marker, Agent], q_marker: Marker) -> list[float]:
    rewards = []
    for _ in range(n_episodes):
        board = new_board()
        while True:
            marker = next_marker_to_place(board)
            action = agents[marker].get_action(state_t=board)
            board = transition(board, action)
            reward = reward_from_board_transition(board)

            if game_state(board) != GameState.INCOMPLETE:
                # Now reward is always from the perspective of the mover,
                # so flip it unless that mover was the Q‑agent:
                rewards.append(reward if marker == q_marker else -reward)
                break
    return rewards


def output_results(rewards: list[float]):
    wins = sum([r == 1.0 for r in rewards])
    ties = sum([r == 0.0 for r in rewards])
    losses = sum([r == -1.0 for r in rewards])
    total = wins + ties + losses

    print(f"win_or_tie_ratio: {(wins+ties) / total}")
    print(f"win_ratio: {wins / total}")
    print(f"tie_ratio: {ties / total}")
    print(f"loss_ratio: {losses/ total}")
    assert total == len(rewards)


def main(n_episodes: int, pretrained_dir: Path, random_seed: int):
    seed(random_seed)

    random_agent = RandomAgent()

    # Decide which Marker is Q‑agent
    q_marker = Marker.FIRST_PLAYER  # when testing as first…
    q_agent = load_q_agent(pretrained_dir, marker=q_marker)
    print("Q Agent as first player:")
    output_results(
        eval(
            n_episodes=n_episodes,
            agents={Marker.FIRST_PLAYER: q_agent, Marker.SECOND_PLAYER: random_agent},
            q_marker=q_marker,  # pass it in
        )
    )

    q_marker = Marker.SECOND_PLAYER  # when testing as second
    q_agent._marker = q_marker
    print("Q Agent as second player:")
    output_results(
        eval(
            n_episodes=n_episodes,
            agents={Marker.FIRST_PLAYER: random_agent, Marker.SECOND_PLAYER: q_agent},
            q_marker=q_marker,  # and here
        )
    )


if __name__ == "__main__":
    cli = ArgumentParser()
    cli.add_argument("--n-episodes", help="how many episodes", type=int, required=True)
    # NOTE: have to save as str because json package doesn't support Path directly
    cli.add_argument(
        "--pretrained-dir", help="dir to load past training artifacts from", type=Path
    )
    cli.add_argument("--seed", help="random seed", type=int, default=42)
    args = cli.parse_args()
    main(
        n_episodes=args.n_episodes,
        pretrained_dir=args.pretrained_dir,
        random_seed=args.seed,
    )
