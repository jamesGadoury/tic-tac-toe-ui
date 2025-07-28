import json
from argparse import ArgumentParser
from pathlib import Path
from time import time_ns

from train import load_q_agent


def copy_q_tables(qtable1, qtable2) -> dict:
    qtable = qtable1
    for k, v in qtable2.items():
        if k not in qtable:
            qtable[k] = v
            continue

        if v != 0.0:
            qtable[k] = v
    return qtable


# TODO: fix when I cleanup marker interface
def main(dir1: Path, dir2: Path, outdir: Path):
    t = time_ns()
    outdir = outdir / f"merge_{t}"
    outdir.mkdir(parents=True)
    agent1 = load_q_agent(dir1)
    agent2 = load_q_agent(dir2)

    t = time_ns()

    pth1 = outdir / f"canonical_q_table.json"
    with open(pth1, "w") as f:
        json.dump(copy_q_tables(agent1.canonical_q_table, agent2.canonical_q_table), f)
    print(f"Saved {pth1}")

    pth2 = outdir / f"q_table.json"
    with open(pth2, "w") as f:
        json.dump(copy_q_tables(agent1.q_table, agent2.q_table), f)
    print(f"Saved {pth2}")


if __name__ == "__main__":
    cli = ArgumentParser()
    cli.add_argument("dir1", type=Path)
    cli.add_argument("dir2", type=Path)
    cli.add_argument("--output-dir", type=Path, default="./outputs")
    args = cli.parse_args()
    main(args.dir1, args.dir2, args.output_dir)
