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

RANDOM_AGENT = "RANDOM_AGENT"
FROZEN_Q_AGENT = "FROZEN_Q_AGENT"


@dataclass
class TrainingParams:
    n_episodes: int
    # TODO: do we use same pretrained dir for frozen and the training agent?
    pretrained_dir: Path | None
    seed: float
    learning_rate_max: float
    learning_rate_min: float
    learning_rate_decay_rate: float
    epsilon_max: float
    epsilon_min: float
    epsilon_decay_rate: float
    opponent: str
    training: Marker


@dataclass
class Transition:
    state_t0: Board
    action: int
    reward: float
    state_t1: Board


@dataclass
class EpisodeResults:
    n_updates: int
    mean_td_error: float
    mean_abs_td_error: float
    mean_squared_td_error: float
    max_abs_td_error: float
    final_reward: float


def reward_from_board_transition(board: Board) -> float:
    # NOTE: if next marker is second player, then first player just played
    first_player: bool = next_marker_to_place(board) == Marker.SECOND_PLAYER
    outcome = game_state(board)
    if outcome == GameState.FIRST_PLAYER_WON:
        return 1.0 if first_player else -1.0
    if outcome == GameState.SECOND_PLAYER_WON:
        return -1.0 if first_player else 1.0
    return 0.0


def _save_obj(obj: Any, path: Path):
    with open(path, "w") as f:
        json.dump(obj, f)


def save(
    q_agent: QAgent,
    episodes: list[EpisodeResults],
    transitions: list[Transition],
    output_dir: Path,
    post_fix: str = "",
):
    _save_obj(
        q_agent.canonical_q_table, output_dir / f"canonical_q_table_{post_fix}.json"
    )
    _save_obj(q_agent.q_table, output_dir / f"q_table_{post_fix}.json")
    _save_obj([asdict(r) for r in episodes], output_dir / f"episodes_{post_fix}.json")
    _save_obj(
        [asdict(t) for t in transitions], output_dir / f"transitions_{post_fix}.json"
    )


def load(dir: Path):
    assert dir.is_dir()
    canonical_q_table_path: Path = dir / "canonical_q_table.json"
    assert canonical_q_table_path.exists()
    q_table_path: Path = dir / "q_table.json"
    assert q_table_path.exists()
    return QAgent.load(
        canonical_q_table=json.load(open(canonical_q_table_path, "r")),
        q_table=json.load(open(q_table_path, "r")),
    )


# TODO: break up script into focused scripts
#  1. self play (with one player frozen)
#  2. random player
#  3. train from past sars transition pairs
#  4. make dir structure more strongly typed somehow
#  5. update all scripts so that we can dynamically load
#     artifacts (e.g. tables) to build training off of
#  6. automatic analysis scripts
#  7. collect training details that show a "trail"
#     e.g. train x -> dir 1, load dir 1 and train y -> dir 2, etc
#     then in whatever dir n, can track back to past dirs and
#     training stats

# TODO: probably should make this a package at this point lol


def play_episode(
    first_player: Agent,
    second_player: Agent,
    training: Marker,
    epsilon: float,
    learning_rate: float,
) -> tuple[EpisodeResults, list[Transition]]:
    agents = {Marker.FIRST_PLAYER: first_player, Marker.SECOND_PLAYER: second_player}
    board: Board = new_board()
    td_errors = []
    transitions: list[Transition] = []
    while True:
        marker = next_marker_to_place(board)
        action = agents[marker].get_action(state_t=board, epsilon=epsilon)
        next_board = transition(board, action)
        reward = reward_from_board_transition(next_board)
        if marker == training:
            td_error = agents[marker].update(
                state_t=board,
                reward=reward,
                action=action,
                state_t_next=next_board,
                learning_rate=learning_rate,
            )
            td_errors.append(td_error)

        transitions.append(
            Transition(
                state_t0=board, action=action, reward=reward, state_t1=next_board
            )
        )

        board = next_board

        if game_state(board) != GameState.INCOMPLETE:
            # terminal
            final_reward = reward if marker == training else -reward
            break

    n = len(td_errors)
    abs_errors = [abs(e) for e in td_errors]
    return (
        EpisodeResults(
            n_updates=n,
            mean_td_error=sum(td_errors) / n,
            mean_abs_td_error=sum(abs_errors) / n,
            mean_squared_td_error=sum([e * e for e in td_errors]) / n,
            max_abs_td_error=max(abs_errors),
            final_reward=final_reward,
        ),
        transitions,
    )


def training_loop(params: TrainingParams, save_every_x_episodes: int, output_dir: Path):
    seed(params.seed)

    _save_obj(asdict(params), output_dir / f"training_params.json")

    # TODO: handle pretrained dir to load artifacts (such as past training params and q tables)
    # TODO: add support for frozen q agent
    assert params.opponent == RANDOM_AGENT, "only random agent supported atm"

    first_player = QAgent() if params.training == Marker.FIRST_PLAYER else RandomAgent()
    second_player = (
        QAgent() if params.training == Marker.SECOND_PLAYER else RandomAgent()
    )

    episodes: list[EpisodeResults] = []
    transitions: list[Transition] = []
    ep: int = 0
    # TODO: for now hardcoding agent as second player, but break this script
    #        into multiple scripts (and entrypoints specific to each training modality)
    for ep in tqdm(range(params.n_episodes)):
        epsilon = params.epsilon_min + (params.epsilon_max - params.epsilon_min) * exp(
            -params.epsilon_decay_rate * ep
        )
        learning_rate = params.learning_rate_min + (
            params.learning_rate_max - params.learning_rate_min
        ) * exp(-params.learning_rate_decay_rate * ep)

        episode_results, episode_transitions = play_episode(
            first_player=first_player,
            second_player=second_player,
            training=params.training,
            epsilon=epsilon,
            learning_rate=learning_rate,
        )

        episodes.append(episode_results)
        transitions += episode_transitions

        if ep % save_every_x_episodes == 0:
            q_agent = (
                first_player
                if params.training == Marker.FIRST_PLAYER
                else second_player
            )
            assert type(q_agent) is QAgent
            save(
                q_agent=q_agent,
                episodes=episodes,
                transitions=transitions,
                output_dir=output_dir,
                post_fix=str(ep),
            )
            # clear out list so that we don't run out of ram
            episodes = []
            transitions = []

    q_agent = first_player if params.training == Marker.FIRST_PLAYER else second_player
    assert type(q_agent) is QAgent
    save(
        q_agent=q_agent,
        episodes=episodes,
        transitions=transitions,
        output_dir=output_dir,
        post_fix=str(ep),
    )


if __name__ == "__main__":
    cli = ArgumentParser()
    cli.add_argument("--n-episodes", help="how many episodes", type=int, required=True)
    cli.add_argument(
        "--pretrained-dir", help="dir to load past training artifacts from", type=Path
    )
    cli.add_argument("--seed", help="random seed", type=int, default=42)
    cli.add_argument(
        "--learning-rate-max", help="max learning rate", type=float, default=0.5
    )
    cli.add_argument(
        "--learning-rate-min", help="min learning rate", type=float, default=0.01
    )
    cli.add_argument(
        "--learning-rate-decay-rate",
        help="decay rate for learning rate",
        type=float,
        default=0.99,
    )
    cli.add_argument(
        "--epsilon-max", help="max probability of exploration", type=float, default=1.0
    )
    cli.add_argument(
        "--epsilon-min", help="min probability of exploration", type=float, default=0.1
    )

    cli.add_argument(
        "--epsilon-decay-rate",
        help="decay rate for probability of exploration",
        type=float,
        default=0.99,
    )

    cli.add_argument(
        "--training",
        type=int,
        choices=[1, 2],
        help="which player is training",
        default=1,
    )
    cli.add_argument(
        "--opponent",
        type=str,
        choices=[RANDOM_AGENT, FROZEN_Q_AGENT],
        help="who is the opponent of the agent that is training",
        default=RANDOM_AGENT,
    )
    cli.add_argument(
        "--save_every_x_episodes",
        help="rate at which we save results",
        type=int,
        default=500_000,
    )
    cli.add_argument(
        "--output-dir",
        help="dir to output files to (note that a new dir will be created within this dir)",
        type=Path,
        default="./outputs",
    )
    args = cli.parse_args()

    output_dir = args.output_dir / str(time_ns())
    output_dir.mkdir(parents=True)

    print(f"Saving all outputs to path: {output_dir}")

    training_loop(
        params=TrainingParams(
            n_episodes=args.n_episodes,
            pretrained_dir=args.pretrained_dir,
            seed=args.seed,
            learning_rate_max=args.learning_rate_max,
            learning_rate_min=args.learning_rate_min,
            learning_rate_decay_rate=args.learning_rate_decay_rate,
            epsilon_max=args.epsilon_max,
            epsilon_min=args.epsilon_min,
            epsilon_decay_rate=args.epsilon_decay_rate,
            opponent=args.opponent,
            training=Marker(args.training),
        ),
        save_every_x_episodes=args.save_every_x_episodes,
        output_dir=output_dir,
    )
