#!/bin/bash
set -euo pipefail

# Base folder under which train.py will create timestamped subdirs
BASE_OUTPUT="./outputs/schedule_run"
mkdir -p "$BASE_OUTPUT"

# No pretrained in phase1
PREV=""

run_phase() {
  local phase_name=$1
  shift
  echo
  echo "===== START PHASE: $phase_name ====="
  if [[ -n "$PREV" ]]; then
    ARGS+=(--pretrained-dir "$PREV")
  fi
  ARGS+=(--output-dir "$BASE_OUTPUT")
  echo "Calling: python train.py ${ARGS[*]}"
  python3 train.py "${ARGS[@]}"
  # pick up the most‐recent subdir under $BASE_OUTPUT
  PREV=$(ls -1dt "$BASE_OUTPUT"/*/ | head -n1)
  echo "→ phase '$phase_name' wrote to: $PREV"
  unset ARGS
}

# 1) Train as first player vs RANDOM_AGENT
ARGS=(--n-episodes 1000000
      --training 1
      --opponent RANDOM_AGENT
      --epsilon-max 1.0
      --epsilon-min 0.1
      --epsilon-decay-rate 0.999)
run_phase "first_vs_random"

# 2) Train as second player vs RANDOM_AGENT (continuing from phase1)
ARGS=(--n-episodes 1000000
      --training 2
      --opponent RANDOM_AGENT
      --epsilon-max 1.0
      --epsilon-min 0.1
      --epsilon-decay-rate 0.999)
run_phase "second_vs_random"

# 3) Self‑play: train as first player against a frozen copy of yourself
ARGS=(--n-episodes 2000000
      --training 1
      --opponent FROZEN_Q_AGENT
      --opponent-pretrained-dir "$PREV"
      --epsilon-max 0.5
      --epsilon-min 0.01
      --epsilon-decay-rate 0.9999)
run_phase "selfplay_first"

# 4) Self‑play: train as second player against that same frozen copy
ARGS=(--n-episodes 2000000
      --training 2
      --opponent FROZEN_Q_AGENT
      --opponent-pretrained-dir "$PREV"
      --epsilon-max 0.5
      --epsilon-min 0.01
      --epsilon-decay-rate 0.9999)
run_phase "selfplay_second"

echo
echo "All done!  Final Q‑tables in: $PREV"
