import json
from argparse import ArgumentParser
from pathlib import Path
from time import time_ns

import numpy as np
import pandas as pd
from agents import QAgent
from tqdm import tqdm
from train import _save_obj, load_q_agent


def iter_transitions(root_dir: Path, pattern: str = "transitions_*.json"):
    assert root_dir.exists() and root_dir.is_dir()
    for path in root_dir.rglob(pattern):
        transition = json.loads(path.read_text())
        if not transition:
            continue
        yield transition


def iter_transition_dfs(root_dir: Path, pattern: str = "transitions_*.json"):
    yield pd.DataFrame(iter_transitions(root_dir=root_dir, pattern=pattern))


def main(
    n_samples: int,
    n_sample_size: int,
    learning_rate: float,
    save_every_x_episodes: int,
    input_dir: Path,
    output_dir: Path,
    pretrained_dir: Path | None,
):
    q_agent = (
        load_q_agent(Path(pretrained_dir)) if pretrained_dir is not None else QAgent()
    )
    td_errors = []
    try:
        for n in tqdm(range(n_sample_size)):
            transitions = next(iter_transitions(root_dir=input_dir))
            if not transitions:
                continue

            for i, transition in enumerate(transitions):
                if i > n_sample_size:
                    break

                td_errors.append(
                    q_agent.update(
                        state_t=tuple(transition["state_t0"]),
                        reward=transition["reward"],
                        action=transition["action"],
                        state_t_next=tuple(transition["state_t1"]),
                        learning_rate=learning_rate,
                    )
                )
    except KeyboardInterrupt as e:
        print("detected keyboard interrupt. closing gracefully")
    except Exception as e:
        print(f"unexpected exception {e}. closing gracefully")

    td_errors = np.array(td_errors)
    abs_td_errors = abs(td_errors)

    metrics = {
        "abs_td_error_p50": float(np.percentile(abs_td_errors, 50)),
        "abs_td_error_p90": float(np.percentile(abs_td_errors, 90)),
        "abs_td_error_max": float(abs_td_errors.max()),
        "abs_td_error_mean": float(abs_td_errors.mean()),
    }
    training_parameters = {
        "learning_rate": learning_rate,
        "n_samples": n_samples,
        "n_sample_size": n_sample_size,
        "pretrained_dir": str(pretrained_dir),
        "description": "offline training using saved transitions",
    }
    _save_obj(q_agent.canonical_q_table, output_dir / f"canonical_q_table.json")
    _save_obj(q_agent.q_table, output_dir / f"q_table.json")
    _save_obj(metrics, output_dir / "metrics.json")
    _save_obj(training_parameters, output_dir / "training_parameters.json")
    for k, v in metrics.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    cli = ArgumentParser()
    cli.add_argument(
        "--n-samples",
        help="how many samples you want to train on",
        type=int,
        required=True,
    )
    cli.add_argument(
        "--n-sample-size",
        help="how much of each sample you want to train on",
        type=int,
        required=True,
    )
    cli.add_argument(
        "--pretrained-dir", help="dir to load past training artifacts from", type=Path
    )

    cli.add_argument(
        "--save_every_x_episodes",
        help="rate at which we save results",
        type=int,
        default=500_000,
    )
    cli.add_argument(
        "--input-dir",
        help="dir to source transitions from",
        type=Path,
        # NOTE: not a bug, we use same default as output-dir as that
        #       is where our transition files are typically going
        default="./outputs",
    )
    cli.add_argument(
        "--output-dir",
        help="dir to output files to (note that a new dir will be created within this dir)",
        type=Path,
        default="./outputs",
    )
    cli.add_argument("--learning-rate", type=float, default=0.05)
    args = cli.parse_args()

    output_dir = args.output_dir / str(time_ns())
    output_dir.mkdir(parents=True)

    print(f"Saving all outputs to path: {output_dir}")
    main(
        n_samples=args.n_samples,
        n_sample_size=args.n_sample_size,
        learning_rate=args.learning_rate,
        save_every_x_episodes=args.save_every_x_episodes,
        input_dir=args.input_dir,
        output_dir=output_dir,
        pretrained_dir=args.pretrained_dir,
    )
