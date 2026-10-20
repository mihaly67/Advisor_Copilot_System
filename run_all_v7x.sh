#!/bin/bash
set -e
SRC=/data/LGBM_copilot/src
LOG=/data/LGBM_copilot
cd $SRC

run() {
  local name=$1; shift
  echo "\n$(date +%H:%M:%S) STARTING: $name"
  python3 -u scalper_optuna_v7x.py "$@" 2>&1 | tee $LOG/v7x_${name}.log
  echo "$(date +%H:%M:%S) DONE: $name"
}

run c25_auc   --contra_max 0.25 --obj auc    --n_trials 40
run c30_auc   --contra_max 0.30 --obj auc    --n_trials 40
run c25_wrauc --contra_max 0.25 --obj wr_auc --n_trials 40
run c20_wrauc --contra_max 0.20 --obj wr_auc --n_trials 40
run c25_ev    --contra_max 0.25 --obj ev     --n_trials 40

echo "\nALL EXPERIMENTS DONE at $(date)"
