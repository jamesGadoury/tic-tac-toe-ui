import logging
from dataclasses import dataclass
from functools import cache
from math import exp
from random import choice, random
from typing import Protocol, cast

from .egocentric import (
    EgocentricBoard,
    EgocentricMarker,
    canonicalize_board_action,
    remap_to_egocentric_board,
)

logger = logging.getLogger(__name__)


@cache
def possible_actions(state_t: EgocentricBoard) -> tuple[int, ...]:
    return tuple(
        idx for idx in range(len(state_t)) if state_t[idx] != EgocentricMarker.EMPTY
    )


@cache
def pretty_format_possible_actions(possible_actions: tuple[int, ...]):
    s = ""
    for i in range(0, 9, 3):
        s += " ".join(
            [
                str(m) if m in possible_actions else "_"
                for m in (
                    i,
                    i + 1,
                    i + 2,
                )
            ]
        )
        s += "\n"
    return s


@cache
def pretty_format_state(state_t: EgocentricBoard) -> str:
    """Output pretty format"""
    keys = {
        EgocentricMarker.EMPTY: "_",
        EgocentricMarker.AGENT: "🤖",
        EgocentricMarker.OPPONENT: "👾",
    }

    s = ""
    for i in range(0, 9, 3):
        s += f"{keys[state_t[i]]} {keys[state_t[i+1]]} {keys[state_t[i+2]]}\n"
    return s


class Agent(Protocol):
    def get_action(self, state_t: EgocentricBoard) -> int: ...


class RandomAgent(Agent):
    def get_action(self, state_t: EgocentricBoard) -> int:
        return choice(possible_actions(state_t))


class HumanAgent(Agent):
    def get_action(self, state_t: EgocentricBoard) -> int:
        possible_actions_t = possible_actions(state_t)

        print("---------------------------------")
        print(f"current board state: \n{pretty_format_state(state_t)}")
        print(
            f"current possible actions: \n{pretty_format_possible_actions(possible_actions_t)}"
        )
        print("your play?")
        play = int(input())
        while play not in possible_actions(state_t):
            print(f"invalid play, please enter one of the available numbers")
            play = int(input())
        return play
