import json
from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path

from train import find_most_recent_file_with_substring


def load_table(path):
    with open(path) as f:
        return json.load(f)


def parse_key(key):
    board = key[:9]
    action = int(key[9])
    return board, action


def analyze_table(table, name):
    boards = defaultdict(list)
    values = []
    illegal = []
    for key, q in table.items():
        board, action = parse_key(key)
        boards[board].append((action, q))
        values.append(q)
        if board[action] != "0":
            illegal.append((board, action, q))
    num_entries = len(table)
    num_boards = len(boards)
    min_q, max_q = min(values), max(values)
    num_zeros = sum(1 for q in values if q == 0)
    missing_info = []
    for board, acts in boards.items():
        empty_positions = {i for i, c in enumerate(board) if c == "0"}
        act_positions = {a for a, _ in acts}
        missing = empty_positions - act_positions
        extra = act_positions - empty_positions
        if missing or extra:
            missing_info.append((board, missing, extra))

    print(f"\n=== {name} ===")
    print(f"Total entries: {num_entries}")
    print(f"Unique boards: {num_boards}")
    print(f"Q-value range: [{min_q:.3f}, {max_q:.3f}]")
    print(f"Zero-value entries: {num_zeros} ({num_zeros/num_entries*100:.1f}%)")
    print(f"Illegal moves logged: {len(illegal)}")
    if illegal:
        print("  Sample illegal entries (board, action, Q):")
        for b, a, q in illegal[:5]:
            print(f"    Board={b}, action={a}, Q={q:.3f}")
    print(f"Boards with missing/extra actions: {len(missing_info)}")
    if missing_info:
        print("  Sample board issues (board, missing, extra):")
        for b, m, e in missing_info[:5]:
            print(f"    Board={b}, missing={m}, extra={e}")

    return boards


def main(training_dir: Path):
    canonical_q_table_pth = find_most_recent_file_with_substring(
        dir=Path(training_dir), substring="canonical_q_table"
    )
    assert canonical_q_table_pth is not None
    q_table_pth = canonical_q_table_pth.with_name(
        canonical_q_table_pth.name.replace("canonical_", "")
    )

    canonical_q_table = json.load(open(canonical_q_table_pth, "r"))
    q_table = json.load(open(q_table_pth, "r"))

    print(f"Loaded {canonical_q_table_pth}")
    print(f"Loaded {q_table_pth}")

    boards_reg = analyze_table(q_table, "Regular Q Table")
    boards_can = analyze_table(canonical_q_table, "Canonical Q Table")

    shared = set(boards_reg) & set(boards_can)
    print(f"\nShared boards between tables: {len(shared)}")
    print("Sample comparisons (board: reg_count vs can_count):")
    for b in list(shared)[:5]:
        print(f"  {b}: {len(boards_reg[b])} vs {len(boards_can[b])}")


if __name__ == "__main__":
    cli = ArgumentParser()
    cli.add_argument(
        "--training-dir", help="dir to load past training artifacts from", type=str
    )
    args = cli.parse_args()
    main(args.training_dir)
