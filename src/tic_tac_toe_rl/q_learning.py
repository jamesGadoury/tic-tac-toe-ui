from collections import defaultdict
from dataclasses import asdict, dataclass
from math import exp
from random import choice, random
from typing import cast

from tic_tac_toe_rl.game_env import GameEnv, Transition
from tic_tac_toe_rl.tic_tac_toe import GameState, Marker

from .agents import (
    Agent,
    possible_actions,
    pretty_format_possible_actions,
    pretty_format_state,
)
from .canonicalization import canonicalize_board_action
from .egocentric import EgocentricBoard, EgocentricMarker

QTable = defaultdict[str, float]


@dataclass
class EpsilonStrategy:
    eps_min: float
    eps_max: float
    decay_rate: float


def serialize_state_action(state_t: EgocentricBoard, action_t: int) -> str:
    return "".join([str(m) for m in state_t] + [str(action_t)])


def canonicalize_and_serialize_state_action(
    state_t: EgocentricBoard, action_t: int
) -> str:
    state_t, action_t = canonicalize_board_action(board=state_t, action=action_t)  # type: ignore
    return "".join([str(m) for m in state_t] + [str(action_t)])


class QAgent(Agent):
    def __init__(
        self,
    ):
        self._canonical_q_table: QTable = defaultdict(float)
        self._q_table: QTable = defaultdict(float)
        self._epsilon = 0.0

    @property
    def epsilon(self):
        return self._epsilon

    @epsilon.setter
    def epsilon(self, value: float):
        self._epsilon = value

    @classmethod
    def load(
        cls,
        canonical_q_table: QTable,
        q_table: QTable,
    ) -> "QAgent":
        agent = QAgent()
        agent._canonical_q_table = canonical_q_table
        agent._q_table = q_table
        return agent

    @property
    def canonical_q_table(self):
        return self._canonical_q_table

    @property
    def q_table(self):
        return self._q_table

    def get_action(self, state_t: EgocentricBoard) -> int:
        if random() < self._epsilon:
            # explore
            return choice(possible_actions(state_t))

        # greedy
        next_qs: list[tuple[int, float]] = []
        for action_t in possible_actions(state_t):
            # NOTE: We need to return the regular action, but we need
            #       to use the action corresponding to the canonicalized board
            #       to create the serialized string to access our canonical table.
            canonical_state_t, canonical_action_t = canonicalize_board_action(
                board=state_t, action=action_t
            )
            canonical_state_action_t = canonicalize_and_serialize_state_action(
                state_t=cast(EgocentricBoard, canonical_state_t),
                action_t=canonical_action_t,
            )
            next_qs.append(
                (
                    action_t,
                    self._canonical_q_table[canonical_state_action_t],
                )
            )

        # TODO: consider randomly selecting from ties
        return max(next_qs, key=lambda t: t[1])[0]


@dataclass
class QTrainerConfig:
    epsilon_strategy: EpsilonStrategy


@dataclass
class QTrainerRecord:
    steps: int = 0
    td_errors: list[float] = []
    N: defaultdict[str, int] = defaultdict(int)


class QTrainer:
    def __init__(
        self, config: QTrainerConfig, agent_in_training: QAgent, opponent: Agent
    ):
        self._config: QTrainerConfig = config
        self._agent_in_training = agent_in_training
        self._opponent = opponent
        self._record = QTrainerRecord()

        # TODO: parse config for strategy to determine who goes first or second
        #       probably want to have some kinda of interleaving training strategy
        #       where opponent and agent in training are swapping who is first or second
        self._agent_in_training_marker: Marker = Marker.FIRST_PLAYER

    def to_dict(self) -> dict:
        return {
            "config": asdict(self._config),
            "record": asdict(self._record),
        }

    def train(self) -> dict:
        # TODO: impl training loop, which should support
        #       1. scheduling different training sessions in same run,
        #            e.g. switching agent in training as first and second player,
        #            different opponents, etc
        #       2. configurable metrics to early stop training and switch to
        #           next part of schedule (also should ideally save off
        #           the last good parameters)
        return self.to_dict()

    def _get_players_by_order(self) -> tuple[Agent, Agent]:
        if self._agent_in_training_marker == Marker.FIRST_PLAYER:
            return self._agent_in_training, self._opponent
        return self._opponent, self._agent_in_training

    def _play_episode(self):
        first_player, second_player = self._get_players_by_order()
        game_env = GameEnv(first_player=first_player, second_player=second_player)

        last_training_state_t0: EgocentricBoard | None = None
        last_training_action_t0: int | None = None
        while True:
            transition: Transition = game_env.update()

            if transition.marker_t0 == self._agent_in_training_marker:
                self._record.steps += 1

                self._agent_in_training.epsilon = (
                    self._config.epsilon_strategy.eps_min
                    + (
                        self._config.epsilon_strategy.eps_max
                        - self._config.epsilon_strategy.eps_min
                    )
                    * exp(
                        -self._record.steps / self._config.epsilon_strategy.decay_rate
                    )
                )
                self._record.td_errors.append(
                    self._update_agent_in_training(transition)
                )
                last_training_state_t0 = transition.state_t0
                last_training_action_t0 = transition.action_t0

            if transition.game_state_t1 != GameState.INCOMPLETE:
                if transition.marker_t0 != self._agent_in_training_marker:
                    # NOTE: we always want to train using transition to terminal state,
                    #       so if this wasn't from the agent in training's actions,
                    #       we update here (otherwise we already would have updated
                    #       above).
                    assert last_training_state_t0 is not None
                    assert last_training_action_t0 is not None
                    updated_transition = transition
                    updated_transition.state_t0 = last_training_state_t0
                    updated_transition.action_t0 = last_training_action_t0
                    self._record.td_errors.append(
                        self._update_agent_in_training(
                            Transition(
                                marker_t0=self._agent_in_training_marker,
                                state_t0=last_training_state_t0,
                                action_t0=last_training_action_t0,
                                # NOTE: we take the negative of the reward because
                                #       if we are in this path this means that the
                                #       opponent played the move, and what is good
                                #       for the opponent is bad for the training
                                #       agent and vice versa.
                                reward_t0=(-1 * transition.reward_t0),
                                state_t1=transition.state_t1,
                                game_state_t1=transition.game_state_t1,
                            )
                        )
                    )
                break

    def _update_q_tables(self, state_t: EgocentricBoard, action_t: int, q_t: float):
        canonical_state_action_t = canonicalize_and_serialize_state_action(
            state_t=state_t, action_t=action_t
        )
        # TODO: double check that we can mutate both tables through property access
        self._agent_in_training.canonical_q_table[canonical_state_action_t] = q_t

        state_action_t = serialize_state_action(state_t=state_t, action_t=action_t)
        self._agent_in_training.q_table[state_action_t] = q_t

    def _update_agent_in_training(self, transition: Transition) -> float:
        """Updates tables and returns td error"""
        canonical_state_action_t0 = canonicalize_and_serialize_state_action(
            state_t=transition.state_t0, action_t=transition.action_t0
        )

        # NOTE: We update learning rate as a function of how many times
        #       this state was visited & updated
        self._record.N[canonical_state_action_t0] += 1

        lr = 1.0 / self._record.N[canonical_state_action_t0]
        q_t0 = self._agent_in_training.canonical_q_table[canonical_state_action_t0]

        if transition.game_state_t1 != GameState.INCOMPLETE:
            # next state is terminal so all q values at next state will be 0
            td_error = transition.reward_t0 - q_t0
            self._update_q_tables(
                state_t=transition.state_t0,
                action_t=transition.action_t0,
                q_t=q_t0 + lr * td_error,
            )
            return td_error

        next_transition_qs: list[float] = []
        for action_t1 in possible_actions(transition.state_t1):
            next_transition_qs.append(
                self._agent_in_training.canonical_q_table[
                    canonicalize_and_serialize_state_action(
                        state_t=transition.state_t1, action_t=action_t1
                    )
                ]
            )

        # TODO: consider randomly selecting from ties
        max_q_t1 = max(next_transition_qs)

        td_error = transition.reward_t0 + max_q_t1 - q_t0
        self._update_q_tables(
            state_t=transition.state_t0,
            action_t=transition.action_t0,
            q_t=q_t0 + lr * td_error,
        )
        return td_error
