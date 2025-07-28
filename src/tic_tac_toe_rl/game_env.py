from dataclasses import asdict, dataclass

from tic_tac_toe_rl.egocentric import EgocentricBoard, remap_to_egocentric_board
from tic_tac_toe_rl.tic_tac_toe import (
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

from .agents import Agent

GAME_STATE_TO_OUTCOMES = {
    GameState.FIRST_PLAYER_WON: "FIRST_PLAYER_WON",
    GameState.SECOND_PLAYER_WON: "SECOND_PLAYER_WON",
    GameState.TIED: "TIED",
}


@dataclass
class Transition:
    marker_t0: Marker
    state_t0: EgocentricBoard
    action_t0: int
    reward_t0: float
    state_t1: EgocentricBoard
    game_state_t1: GameState


def reward_from_board_transition(board_t1: Board, marker_t0: Marker) -> float:
    is_first_player: bool = marker_t0 == Marker.FIRST_PLAYER
    outcome = game_state(board_t1)
    if outcome == GameState.FIRST_PLAYER_WON:
        return 1.0 if is_first_player else -1.0
    if outcome == GameState.SECOND_PLAYER_WON:
        return -1.0 if is_first_player else 1.0
    return 0.0


class GameEnv:
    def __init__(self, first_player: Agent, second_player: Agent):
        self._players = {
            Marker.FIRST_PLAYER: first_player,
            Marker.SECOND_PLAYER: second_player,
        }
        self._outcome: str = ""
        self._board: Board = new_board()

    def update(self) -> Transition:
        if self._outcome:
            raise RuntimeError(
                f"update called on completed game with outcome {self._outcome}"
            )

        marker_t0 = next_marker_to_place(self._board)
        state_t0 = remap_to_egocentric_board(board=self._board, agent_marker=marker_t0)
        action_t0 = self._players[marker_t0].get_action(state_t=state_t0)
        if action_t0 not in available_plays(self._board):
            raise RuntimeError(
                f"{action_t0} is not a valid play for: \n{pretty_format(self._board)}"
            )

        self._board = transition(self._board, action_t0)
        state_t1 = remap_to_egocentric_board(board=self._board, agent_marker=marker_t0)
        reward_t0 = reward_from_board_transition(
            board_t1=self._board, marker_t0=marker_t0
        )

        if game_state(self._board) != GameState.INCOMPLETE:
            self.outcome = GAME_STATE_TO_OUTCOMES[game_state(self._board)]

        return Transition(
            marker_t0=marker_t0,
            state_t0=state_t0,
            action_t0=action_t0,
            reward_t0=reward_t0,
            state_t1=state_t1,
            game_state_t1=game_state(self._board),
        )
