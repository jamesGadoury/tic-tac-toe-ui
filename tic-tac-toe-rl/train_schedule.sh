#!/usr/bin/env bash
set -euo pipefail

# Base folder for timestamped subdirs
BASE_OUTPUT="./outputs/schedule_run"
mkdir -p "$BASE_OUTPUT"
PREV=""

run_phase() {
  local phase_name=$1; shift
  echo
  echo "===== START PHASE: $phase_name ====="
  # build args array from remaining parameters
  local ARGS=("$@")
  # if a previous model exists, use it
  if [[ -n "$PREV" ]]; then
    ARGS+=(--pretrained-dir "$PREV")
  fi
  # always point to the same base output
  ARGS+=(--output-dir "$BASE_OUTPUT")
  echo "Calling: python train.py ${ARGS[*]}"
  python3 train.py "${ARGS[@]}"
  # grab the newest subdirectory
  PREV=$(ls -1dt "$BASE_OUTPUT"/*/ | head -n1)
  echo "→ phase '$phase_name' wrote to: $PREV"
}

# 1) First player vs random
run_phase first_vs_random \
  --n-episodes 2000000 \
  --training 1 \
  --opponent RANDOM_AGENT \
  --epsilon-max 1.0 \
  --epsilon-min 0.1 \
  --epsilon-decay-rate 0.999

# 2) Long second vs random (boost coverage)
run_phase second_vs_random_long \
  --n-episodes 4000000 \
  --training 2 \
  --opponent RANDOM_AGENT \
  --epsilon-max 1.0 \
  --epsilon-min 0.1 \
  --epsilon-decay-rate 0.999

# 3) Tight epsilon second vs random (fine-tune)
run_phase second_vs_random_tight \
  --n-episodes 2000000 \
  --training 2 \
  --opponent RANDOM_AGENT \
  --epsilon-max 1.0 \
  --epsilon-min 0.01 \
  --epsilon-decay-rate 0.9995

# 4) Self-play first vs frozen-second
run_phase selfplay_first \
  --n-episodes 4000000 \
  --training 1 \
  --opponent FROZEN_Q_AGENT \
  --opponent-pretrained-dir "$PREV" \
  --epsilon-max 0.5 \
  --epsilon-min 0.01 \
  --epsilon-decay-rate 0.9999

# 5) Extended self-play second vs frozen-first
run_phase selfplay_second_long \
  --n-episodes 6000000 \
  --training 2 \
  --opponent FROZEN_Q_AGENT \
  --opponent-pretrained-dir "$PREV" \
  --epsilon-max 0.5 \
  --epsilon-min 0.01 \
  --epsilon-decay-rate 0.9999

# 6) Final polish: short second vs random with minimal exploration
run_phase second_vs_random_final \
  --n-episodes 1000000 \
  --training 2 \
  --opponent RANDOM_AGENT \
  --epsilon-max 0.2 \
  --epsilon-min 0.0 \
  --epsilon-decay-rate 0.9999

echo
echo "All done! Final model in: $PREV"
