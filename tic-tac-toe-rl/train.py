import json
import logging
import traceback
from argparse import ArgumentParser
from dataclasses import asdict, dataclass
from enum import IntEnum
from math import exp
from pathlib import Path
from random import choice, seed
from sys import stderr
from time import time_ns
from typing import Any, Protocol

from agents import Agent, HumanAgent, QAgent, RandomAgent
from tic_tac_toe import (
    Board,
    GameState,
    Marker,
    available_plays,
    game_state,
    new_board,
    next_marker_to_place,
    pretty_format,
    transition,
)
from tqdm import tqdm

RANDOM_AGENT = "RANDOM_AGENT"
FROZEN_Q_AGENT = "FROZEN_Q_AGENT"
HUMAN_AGENT = "HUMAN_AGENT"

logger = logging.getLogger(__name__)


# TODO: move to a shared file so other scripts can use it (e.g. app_setup.py ?)
def configure_logging(verbose: int, log_file: str | None):
    # map count to levels: 0→WARNING, 1→INFO, 2+→DEBUG
    level = {0: logging.WARNING, 1: logging.INFO}.get(verbose, logging.DEBUG)

    # TODO: land on which fmt, consider switching to json based format
    # fmt = "%(asctime)s %(levelname)-5s [%(name)s] %(message)s"
    fmt = "[%(asctime)s %(levelname)-5s %(filename)s:%(lineno)d] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    handlers: list[logging.Handler] = []
    # always log to console unless a file is forced?
    handlers.append(logging.StreamHandler(stderr))

    if log_file:
        # append instead of overwrite; you can tweak mode="w" if you prefer
        handlers.append(logging.FileHandler(log_file, mode="a"))

    logging.basicConfig(level=level, format=fmt, datefmt=datefmt, handlers=handlers)


@dataclass
class TrainingParams:
    n_episodes: int
    # TODO: do we use same pretrained path for frozen and the training agent?
    pretrained_dir: str | None
    opponent_pretrained_dir: str | None
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


# TODO: update saving logic to use pandas & parquet (or feather) instead of json
# TODO: update to make sure that ctrl+c always exits to save last set of artifacts (e.g. using a sigint_handler)
def _save_obj(obj: Any, path: Path):
    with open(path, "w") as f:
        json.dump(obj, f)


def save(
    q_agent: QAgent,
    episodes: list[EpisodeResults],
    output_dir: Path,
    post_fix: str = "",
):
    _save_obj(
        q_agent.canonical_q_table, output_dir / f"canonical_q_table_{post_fix}.json"
    )
    _save_obj(q_agent.q_table, output_dir / f"q_table_{post_fix}.json")
    _save_obj([asdict(r) for r in episodes], output_dir / f"episodes_{post_fix}.json")


# TODO: break up script into focused scripts
#  1. make dir structure more strongly typed somehow
#  2. automatic analysis scripts

# TODO: probably should make this a package at this point lol


def play_episode(
    first_player: Agent,
    second_player: Agent,
    training: Marker,
    epsilon: float,
    learning_rate: float,
) -> EpisodeResults:
    logger.debug(
        f"\n{first_player=}\n{second_player=}\n{training=}\n{epsilon=}\n{learning_rate=}"
    )
    agents = {Marker.FIRST_PLAYER: first_player, Marker.SECOND_PLAYER: second_player}
    board: Board = new_board()
    td_errors = []
    # NOTE: we need to track the last state and action pair that
    #       the training agent executed so that we can make a
    #       final update on terminal transition
    last_training_s, last_training_a = None, None
    while True:
        logger.debug(f"board at beginning of play: \n{pretty_format(board)}")
        marker = next_marker_to_place(board)
        action = agents[marker].get_action(state_t=board, epsilon=epsilon)
        next_board = transition(board, action)
        reward = reward_from_board_transition(next_board)
        logger.debug(
            f"\ntransition for after player {marker} played: \n\t{agents[marker]=}\n\t{action=}\n\t{reward=}\nnext state:\n{pretty_format(next_board)}\n"
        )
        if marker == training:
            last_training_s, last_training_a = board, action
            td_error = agents[marker].update(
                state_t=board,
                reward=reward,
                action=action,
                state_t_next=next_board,
                learning_rate=learning_rate,
            )
            td_errors.append(td_error)

        if game_state(next_board) != GameState.INCOMPLETE:
            # terminal
            final_reward = reward if marker == training else -reward

            logger.debug(
                f"{marker} played and brought game to terminal state {game_state(next_board)=}, {final_reward=}"
            )
            if marker != training:
                # NOTE: we always update the agent that is training on terminal move if it didn't update this play (e.g. did not make last move)
                assert last_training_s is not None
                assert last_training_a is not None
                td_error = agents[training].update(
                    state_t=last_training_s,
                    reward=final_reward,
                    action=last_training_a,
                    state_t_next=next_board,
                    learning_rate=learning_rate,
                )
                td_errors.append(td_error)
            break

        board = next_board

    logger.debug(f"{td_errors=}")
    n = len(td_errors)
    abs_errors = [abs(e) for e in td_errors]
    return EpisodeResults(
        n_updates=n,
        mean_td_error=sum(td_errors) / n,
        mean_abs_td_error=sum(abs_errors) / n,
        mean_squared_td_error=sum([e * e for e in td_errors]) / n,
        max_abs_td_error=max(abs_errors),
        final_reward=final_reward,
    )


def find_most_recent_file_with_substring(dir: Path, substring: str) -> Path | None:
    """
    Search recursively in `directory` for files whose name contains `substring`
    and return the one with the most recent modification time.
    If no such file exists, return None.
    """
    # Gather all matching files
    matches = [p for p in dir.rglob(f"*{substring}*") if p.is_file()]
    if not matches:
        return None

    # Pick the file with the max mtime
    most_recent = max(matches, key=lambda p: p.stat().st_mtime)
    return most_recent


def load_q_agent(pretrained_dir: Path, frozen: bool = False) -> QAgent:
    assert pretrained_dir is not None

    # NOTE: very hacky, have to search for canonical first because q_table will match both canonical and regular q tables
    canonical_q_table_pth = find_most_recent_file_with_substring(
        dir=Path(pretrained_dir), substring="canonical_q_table"
    )
    assert canonical_q_table_pth is not None
    q_table_pth = canonical_q_table_pth.with_name(
        canonical_q_table_pth.name.replace("canonical_", "")
    )

    canonical_q_table = json.load(open(canonical_q_table_pth, "r"))
    q_table = json.load(open(q_table_pth, "r"))

    logger.info(f"Loaded {canonical_q_table_pth}")
    logger.info(f"Loaded {q_table_pth}")

    return QAgent.load(
        canonical_q_table=canonical_q_table, q_table=q_table, frozen=frozen
    )


def training_loop(params: TrainingParams, save_every_x_episodes: int, output_dir: Path):
    seed(params.seed)

    assert output_dir.exists() and output_dir.is_dir()

    _save_obj(asdict(params), output_dir / f"training_params.json")

    q_agent = (
        load_q_agent(Path(params.pretrained_dir))
        if params.pretrained_dir is not None
        else QAgent()
    )
    opponent = (
        RandomAgent()
        if params.opponent == RANDOM_AGENT
        else (
            (
                QAgent.load(
                    canonical_q_table=q_agent.canonical_q_table,
                    q_table=q_agent.q_table,
                    frozen=True,
                )
                if params.opponent_pretrained_dir is None
                else load_q_agent(Path(params.opponent_pretrained_dir), frozen=True)
            )
            if params.opponent == FROZEN_Q_AGENT
            else HumanAgent()
        )
    )

    first_player, second_player = (
        (
            q_agent,
            opponent,
        )
        if params.training == Marker.FIRST_PLAYER
        else (
            opponent,
            q_agent,
        )
    )

    episodes: list[EpisodeResults] = []
    ep: int = 0

    try:
        for ep in tqdm(range(params.n_episodes)):
            # TODO: change eps and lr to be tracked by training
            #       agent so that they can decay them on every
            #       one of their updates (not per episode).
            #       Either make a TrainingAgent wrapper or
            #       just move the logic to the QAgent and
            #       remove eps and lr from relevant interfaces.
            epsilon = params.epsilon_min + (
                params.epsilon_max - params.epsilon_min
            ) * exp(-params.epsilon_decay_rate * ep)
            learning_rate = params.learning_rate_min + (
                params.learning_rate_max - params.learning_rate_min
            ) * exp(-params.learning_rate_decay_rate * ep)

            episode_results = play_episode(
                first_player=first_player,
                second_player=second_player,
                training=params.training,
                epsilon=epsilon,
                learning_rate=learning_rate,
            )

            episodes.append(episode_results)

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
                    output_dir=output_dir,
                    post_fix=str(ep),
                )
                # clear out list so that we don't run out of ram
                episodes = []
    except KeyboardInterrupt as e:
        print("encountered keyboard interrupt, finalizing outputs")
    except Exception as e:
        print(f"encountered unexpected exception {e}")
        traceback.print_exc()
        print("finalizing outputs...")

    q_agent = first_player if params.training == Marker.FIRST_PLAYER else second_player
    assert type(q_agent) is QAgent
    save(
        q_agent=q_agent,
        episodes=episodes,
        output_dir=output_dir,
        post_fix=str(ep),
    )


if __name__ == "__main__":
    cli = ArgumentParser()
    cli.add_argument("--n-episodes", help="how many episodes", type=int, required=True)
    # NOTE: have to save as str because json package doesn't support Path directly
    cli.add_argument(
        "--pretrained-dir", help="dir to load past training artifacts from", type=str
    )
    cli.add_argument(
        "--opponent-pretrained-dir",
        help="dir to load past training artifacts from for opponent",
        type=str,
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
        choices=[RANDOM_AGENT, FROZEN_Q_AGENT, HUMAN_AGENT],
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
    cli.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase log verbosity (use -vv for DEBUG)",
    )
    cli.add_argument(
        "--log-file",
        metavar="PATH",
        help="Write logs to PATH instead of stderr",
    )
    args = cli.parse_args()

    configure_logging(args.verbose, args.log_file)

    logger.debug("Debug logging is enabled")

    output_dir = args.output_dir / str(time_ns())
    output_dir.mkdir(parents=True)

    print(f"Saving all outputs to path: {output_dir}")

    training_loop(
        params=TrainingParams(
            n_episodes=args.n_episodes,
            pretrained_dir=args.pretrained_dir,
            opponent_pretrained_dir=args.opponent_pretrained_dir,
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
