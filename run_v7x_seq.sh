#!/bin/bash
export PYTHONUNBUFFERED=1
source /home/Jules/jules_venv/bin/activate
SRC=/data/LGBM_copilot/src
L=/data/LGBM_copilot

run_one() {
  local name=$1; shift
  echo "$(date +%H:%M:%S) START $name"
  cd $SRC && python3 -u scalper_optuna_v7x.py "$@" 2>&1 | tee $L/v7x_${name}.log
  echo "$(date +%H:%M:%S) END $name (rc=$?)"
}

run_one c25_auc   --contra_max 0.25 --obj auc    --n_trials 40
run_one c30_auc   --contra_max 0.30 --obj auc    --n_trials 40
run_one c25_wrauc --contra_max 0.25 --obj wr_auc --n_trials 40
run_one c20_wrauc --contra_max 0.20 --obj wr_auc --n_trials 40
run_one c25_ev    --contra_max 0.25 --obj ev     --n_trials 40

echo "$(date +%H:%M:%S) ALL DONE"
