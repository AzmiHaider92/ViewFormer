#!/bin/bash
#SBATCH -J cb_ft
#SBATCH -o %x.%j.out
#SBATCH -e %x.%j.err
#SBATCH -G 5
#SBATCH --nodes 1

# You can start a container on each node from a shared squashfs file
srun --gpus=5 --container-image=/users/rosenbaum/aheidar/containers/tensorflow:21.07-tf2-py3.sqsh --container-save=/users/rosenbaum/aheidar/containers/tensorflow:21.07-tf2-py3.sqsh --container-mounts=/users/rosenbaum/aheidar/code/ViewFormer:/mnt/ViewFormer -w dgx02 --pty /bin/bash -c "python /mnt/ViewFormer/viewformer/cli.py train codebook --job-dir "/mnt/ViewFormer/sm7-codebook-v6" --dataset "/mnt/ViewFormer/datasets/sm7" --resume-from-checkpoint "/mnt/ViewFormer/sm7-codebook-v3/last.ckpt" --num-gpus 5 --batch-size 64 --n-embed 1024 --learning-rate 1.584e-3 --total-steps 800000 --num-val-workers 5 --num-workers 5 --wandb --wandb-exp-name "V6-1m-steps" --wandb-proj-name "codebook_finetune_sm7" "

