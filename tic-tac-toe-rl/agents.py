import logging
from dataclasses import dataclass
from math import exp
from random import choice, random
from typing import Protocol

from egocentric import EgocentricBoard, canonicalize, remap_to_egocentric_board
from tic_tac_toe import (
    Board,
    GameState,
    available_plays,
    game_state,
    pretty_format,
    transition,
)

logger = logging.getLogger(__name__)


class Agent(Protocol):
    def get_action(self, state_t: Board) -> int: ...

    def update(self, state_t, reward, action, state_t_next) -> float | None: ...


class RandomAgent(Agent):
    def get_action(self, state_t: Board) -> int:
        return choice(available_plays(state_t))

    def update(self, state_t, reward, action, state_t_next) -> float | None:
        return None


class HumanAgent(Agent):
    def get_action(self, state_t: Board) -> int:
        available_plays_t = available_plays(state_t)

        def _pretty_format_available_plays():
            s = ""
            for i in range(0, 9, 3):
                s += " ".join(
                    [
                        str(m) if m in available_plays_t else "_"
                        for m in (
                            i,
                            i + 1,
                            i + 2,
                        )
                    ]
                )
                s += "\n"
            return s

        print("---------------------------------")
        print(f"current board: \n{pretty_format(state_t)}")
        print(f"available plays: \n{_pretty_format_available_plays()}")
        print("your play?")
        play = int(input())
        while play not in available_plays(state_t):
            play = int(input())
        return play

    def update(self, state_t, reward, action, state_t_next) -> float | None:
        return None


QTable = dict[str, float]


@dataclass
class EpsilonStrategy:
    eps_min: float
    eps_max: float
    decay_rate: float


class QAgent(Agent):
    def __init__(
        self, epsilon_strategy: EpsilonStrategy | None = None, frozen: bool = False
    ):
        self._canonical_q_table: QTable = {}
        self._q_table: QTable = {}
        self._frozen: bool = frozen
        self._N: dict[str, int] = {}
        self._epsilon_strategy = epsilon_strategy
        self._steps = 0

        logger.debug(f"{self._frozen=}")
        logger.debug(f"{self._epsilon_strategy=}")

    @classmethod
    def load(
        cls,
        canonical_q_table: QTable,
        q_table: QTable,
        epsilon_strategy: EpsilonStrategy | None = None,
        frozen: bool = False,
    ) -> "QAgent":
        # TODO: should frozen have epsilon_strategy? should it ever not move greedy
        learner = QAgent(epsilon_strategy=epsilon_strategy, frozen=frozen)
        learner._canonical_q_table = canonical_q_table
        learner._q_table = q_table
        return learner

    @property
    def canonical_q_table(self):
        return self._canonical_q_table

    @property
    def q_table(self):
        return self._q_table

    def serialize_state_action(self, state: Board, action: int) -> tuple[str, str]:
        """Returns the serialized canonical state action pair and the serialized state action pair"""

        def _serialize_state_action(ego_state: EgocentricBoard, action: int):
            return "".join([str(m) for m in ego_state] + [str(action)])

        ego_state: EgocentricBoard = remap_to_egocentric_board(state)
        canonical_state: EgocentricBoard = canonicalize(ego_state)
        canonical_state_action: str = _serialize_state_action(canonical_state, action)

        # NOTE: we only initialize the canonical q table entry because we
        #       will only ever set entries in the regular q table
        if canonical_state_action not in self._canonical_q_table:
            self._canonical_q_table[canonical_state_action] = 0.0
            self._N[canonical_state_action] = 0

        return canonical_state_action, _serialize_state_action(ego_state, action)

    def get_action(self, state_t: Board) -> int:
        self._steps += 1
        self._epsilon = (
            0.0
            if self._epsilon_strategy is None
            else self._epsilon_strategy.eps_min
            + (self._epsilon_strategy.eps_max - self._epsilon_strategy.eps_min)
            * exp(-self._steps / self._epsilon_strategy.decay_rate)
        )
        if random() < self._epsilon:
            # explore
            return choice(available_plays(state_t))

        # greedy
        next_qs: list[tuple[int, float]] = []
        for action in available_plays(state_t):
            canon_state_action_t, _ = self.serialize_state_action(
                state=state_t, action=action
            )
            next_qs.append(
                (
                    action,
                    self._canonical_q_table[canon_state_action_t],
                )
            )

        # TODO: consider randomly selecting from ties
        return max(next_qs, key=lambda t: t[1])[0]

    def _update_q_tables(self, state: Board, action: int, q: float):
        canonical_state_action_t, state_action_t = self.serialize_state_action(
            state=state, action=action
        )
        self._canonical_q_table[canonical_state_action_t] = q
        self._q_table[state_action_t] = q

    def update(
        self,
        state_t: Board,
        reward: float,
        action: int,
        state_t_next: Board,
        discount_factor: float = 1.0,
    ) -> float | None:
        """Updates tables and returns td error

        If frozen then no updates will be made and no td error will be output.
        """
        if self._frozen:
            return None

        canonical_state_action_t, _ = self.serialize_state_action(
            state=state_t, action=action
        )

        # NOTE: We update learning rate as a function of how many times
        #       this state was visited & updated
        self._N[canonical_state_action_t] += 1
        lr = 1.0 / self._N[canonical_state_action_t]
        q_t = self._canonical_q_table[canonical_state_action_t]

        if game_state(state_t_next) != GameState.INCOMPLETE:
            # next state is terminal so all q values at next state will be 0
            td_error = reward - q_t
            self._update_q_tables(state=state_t, action=action, q=q_t + lr * td_error)
            return td_error

        next_transition_qs: list[float] = []
        for action_next in available_plays(state_t_next):
            canonical_state_action_t_next, _ = self.serialize_state_action(
                state=transition(board=state_t_next, idx=action_next),
                action=action_next,
            )
            next_transition_qs.append(
                self._canonical_q_table[canonical_state_action_t_next]
            )

        # TODO: consider randomly selecting from ties
        max_q_next = max(next_transition_qs)

        td_error = reward + discount_factor * max_q_next - q_t
        self._update_q_tables(state=state_t, action=action, q=q_t + lr * td_error)
        return td_error
