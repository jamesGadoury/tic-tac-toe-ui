import json
from argparse import ArgumentParser
from dataclasses import asdict, dataclass
from pathlib import Path
from random import choice, seed
from time import time_ns
from typing import Any

from q_learning import QLearner
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


@dataclass
class TrainingParams:
    n_episodes: int
    pretrained_dir: Path | None
    seed: float
    learning_rate: float
    epsilon: float


def save(
    q_learner: QLearner,
    training_params: TrainingParams,
    training_stats: dict,
    output_dir: Path,
):
    def _save_obj(obj: Any, path: Path):
        with open(path, "w") as f:
            json.dump(obj, f)
        print(f"Saved {path}")

    _save_obj(q_learner.canonical_q_table, output_dir / "canonical_q_table.json")
    _save_obj(q_learner.q_table, output_dir / "q_table.json")
    _save_obj(training_stats["td_error"], output_dir / "td_error.json")
    _save_obj(training_stats["outcomes"], output_dir / "outcomes.json")
    _save_obj(training_stats["transitions"], output_dir / "transitions.json")
    _save_obj(asdict(training_params), output_dir / "training_params.json")


def load(dir: Path):
    assert dir.is_dir()
    canonical_q_table_path: Path = dir / "canonical_q_table.json"
    assert canonical_q_table_path.exists()
    q_table_path: Path = dir / "q_table.json"
    assert q_table_path.exists()
    return QLearner.load(
        canonical_q_table=json.load(open(canonical_q_table_path, "r")),
        q_table=json.load(open(q_table_path, "r")),
    )


def q_learner_play(
    q_learner: QLearner,
    state_t: Board,
    epsilon: float,
    learning_rate: float,
    training_stats: dict,
) -> Board:
    action = q_learner.get_action(state_t=state_t, epsilon=epsilon)
    next_board = transition(state_t, action)
    reward = reward_from_board_transition(board=next_board)
    q_learner.update(
        state_t=state_t,
        reward=reward,
        action=action,
        state_t_next=next_board,
        learning_rate=learning_rate,
        training_stats=training_stats,
    )
    # TODO: really this should be a dataclass not a dict, maybe
    #       can typedef that something should have a member?
    training_stats["transitions"].append((state_t, action, reward, next_board))
    return next_board


def random_agent_play(state_t: Board) -> Board:
    return transition(board=state_t, idx=choice(available_plays(state_t)))


def reward_from_board_transition(board: Board) -> float:
    # NOTE: if next marker is second player, then first player just played
    first_player: bool = next_marker_to_place(board) == Marker.SECOND_PLAYER
    outcome = game_state(board)
    if outcome == GameState.FIRST_PLAYER_WON:
        return 1.0 if first_player else -1.0
    if outcome == GameState.SECOND_PLAYER_WON:
        return -1.0 if first_player else 1.0
    return 0.0


def rollout_self_play(
    q_learner: QLearner, epsilon: float, learning_rate: float, training_stats: dict
):
    board: Board = new_board()
    while True:
        board = q_learner_play(
            q_learner=q_learner,
            state_t=board,
            epsilon=epsilon,
            learning_rate=learning_rate,
            training_stats=training_stats,
        )
        if game_state(board) != GameState.INCOMPLETE:
            # terminal
            break
    return game_state(board)


def rollout_random_opponent(
    q_learner: QLearner,
    epsilon: float,
    learning_rate: float,
    agent_is_first_player: bool,
    training_stats: dict,
):
    board: Board = new_board()
    while True:
        if next_marker_to_place(board) == Marker.FIRST_PLAYER:
            board = (
                q_learner_play(
                    q_learner=q_learner,
                    state_t=board,
                    epsilon=epsilon,
                    learning_rate=learning_rate,
                    training_stats=training_stats,
                )
                if agent_is_first_player
                else random_agent_play(state_t=board)
            )
        else:
            board = (
                q_learner_play(
                    q_learner=q_learner,
                    state_t=board,
                    epsilon=epsilon,
                    learning_rate=learning_rate,
                    training_stats=training_stats,
                )
                if not agent_is_first_player
                else random_agent_play(state_t=board)
            )
        if game_state(board) != GameState.INCOMPLETE:
            # terminal
            break
    return game_state(board)


def training_loop(params: TrainingParams, output_dir: Path):
    seed(params.seed)

    # TODO: handle pretrained dir to load artifacts (such as past training params and q tables)
    q_learner = QLearner()

    training_stats = {"td_error": [], "outcomes": [], "transitions": []}

    # TODO: for now hardcoding agent as second player, but break this script
    #        into multiple scripts (and entrypoints specific to each training modality)
    for ep in range(params.n_episodes):
        outcome = rollout_random_opponent(
            q_learner=q_learner,
            epsilon=params.epsilon,
            learning_rate=params.learning_rate,
            agent_is_first_player=False,
            training_stats=training_stats,
        )
        training_stats["outcomes"].append(outcome)

    save(
        q_learner=q_learner,
        training_params=params,
        training_stats=training_stats,
        output_dir=output_dir,
    )


if __name__ == "__main__":
    cli = ArgumentParser()
    cli.add_argument("--n-episodes", help="how many episodes", type=int, required=True)
    cli.add_argument(
        "--pretrained-dir", help="dir to load past training artifacts from", type=Path
    )
    cli.add_argument("--seed", help="random seed", type=int, default=42)
    cli.add_argument("--learning-rate", help="learning rate", type=float, default=0.05)
    cli.add_argument(
        "--epsilon", help="probability of exploration", type=float, default=0.1
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
    training_loop(
        params=TrainingParams(
            n_episodes=args.n_episodes,
            pretrained_dir=args.pretrained_dir,
            seed=args.seed,
            learning_rate=args.learning_rate,
            epsilon=args.epsilon,
        ),
        output_dir=output_dir,
    )
