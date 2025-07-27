from dataclasses import dataclass
from pathlib import Path

from tic_tac_toe import Board


@dataclass
class TrainingParams:
    n_episodes: int
    pretrained_dir: Path | None
    seed: float
    learning_rate_max: float
    learning_rate_min: float
    learning_rate_decay_rate: float
    epsilon_max: float
    epsilon_min: float
    epsilon_decay_rate: float


@dataclass
class EpisodeResults:
    td_error: float
    state_t0: Board
    action: int
    reward: float
    state_t1: Board
