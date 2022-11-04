#!/usr/bin/env bash

set -e

export WORKDIR="/workspace/EECS 6414/EECS-6414-Project/backend"
cd "$WORKDIR"

export PYTHONPATH="$WORKDIR/src"
export CUDA_VISIBLE_DEVICES=1
/home/azalea/.conda/envs/vtb/bin/python src/bot/main.py
