from functools import cache


def rotate90(s: tuple[int, ...]) -> tuple[int, ...]:
    return (
        s[6],
        s[3],
        s[0],
        s[7],
        s[4],
        s[1],
        s[8],
        s[5],
        s[2],
    )


def flip(s: tuple[int, ...]) -> tuple[int, ...]:
    return (
        s[2],
        s[1],
        s[0],
        s[5],
        s[4],
        s[3],
        s[8],
        s[7],
        s[6],
    )


# 1) Build the action‐index maps by “spot‐and‐track”:
def make_index_map(transform):
    M = {}
    for old in range(9):
        # make a “one‐hot” board with a marker at `old`
        one = [0] * 9
        one[old] = 1
        new = transform(tuple(one))
        # find where that 1 ended up
        new_idx = new.index(1)
        M[old] = new_idx
    return M


ROT90_ACTION = make_index_map(rotate90)  # e.g. {0:2, 1:5, 2:8, …}
FLIP_ACTION = make_index_map(flip)  # e.g. {0:2, 1:1, 2:0, …}


@cache
def canonicalize_board_action(
    board: tuple[int, ...], action: int
) -> tuple[tuple[int, ...], int]:
    best: tuple[tuple[int, ...], int] | None = (
        None  # will hold (canon_board, canon_action)
    )
    # try all 4 rotations
    b_rot, a_rot = board, action
    for _ in range(4):
        # also try the flipped version
        b_flip = flip(b_rot)
        a_flip = FLIP_ACTION[a_rot]
        for b_candidate, a_candidate in ((b_rot, a_rot), (b_flip, a_flip)):
            pair = (b_candidate, a_candidate)
            if best is None or pair < best:
                best = pair
        # rotate for next iteration
        b_rot, a_rot = rotate90(b_rot), ROT90_ACTION[a_rot]

    assert best is not None
    return best  # (canonical_board, canonical_action)
