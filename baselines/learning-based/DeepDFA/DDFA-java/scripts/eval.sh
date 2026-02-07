#!/bin/bash

set -e
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libtinfo.so.6
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$LD_LIBRARY_PATH"
export PYTHONPATH="$PWD:$PYTHONPATH"
export PATH="./joern-cli":$PATH
# Start singularity instance
python -u sastvd/scripts/prepare.py --dataset vulweaver --global_workers 12

if [ ! -z "$SLURM_ARRAY_TASK_ID"]
then
    jan="--job_array_number $SLURM_ARRAY_TASK_ID"
else
    jan=""
fi
# 'switchWorkspace("workers/getgraphs/all")'
# Start singularity instance
python -u sastvd/scripts/getgraphs.py vulweaver --num_jobs 100 --workers 32

python -u sastvd/scripts/dbize.py --dsname vulweaver
python -u sastvd/scripts/dbize_graphs.py --dsname vulweaver


python -u sastvd/scripts/abstract_dataflow_full.py --dsname vulweaver --workers 16 --no-cache --stage 1
python -u sastvd/scripts/abstract_dataflow_full.py --dsname vulweaver --workers 16 --no-cache --stage 2


python -u sastvd/scripts/dbize_absdf.py --dsname vulweaver


python code_gnn/main_cli.py fit --config configs/config_vulweaver.yaml --config configs/config_ggnn.yaml --seed_everything 1

