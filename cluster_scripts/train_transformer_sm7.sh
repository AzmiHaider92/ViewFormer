#!/bin/bash
#SBATCH -J transformer
#SBATCH -o %x.%j.out
#SBATCH -e %x.%j.err
#SBATCH -G 4
#SBATCH --nodes 1

# You can start a container on each node from a shared squashfs file
srun --mpi=pmix --gpus=4 --container-image=/users/rosenbaum/aheidar/containers/tensorflow:21.07-tf2-py3.sqsh --container-save=/users/rosenbaum/aheidar/containers/tensorflow:21.07-tf2-py3.sqsh --container-mounts=/users/rosenbaum/aheidar/code/ViewFormer:/mnt/ViewFormer -w dgx01 --pty /bin/bash -c "python /mnt/ViewFormer/viewformer/cli.py train transformer --dataset "/mnt/ViewFormer/sm7-code-represenation" --codebook-model "/mnt/ViewFormer/sm7-codebook-v3/last.ckpt" --sequence-size 6 --n-loss-skip 1 --batch-size 128 --fp16 --total-steps 120000 --localization-weight 0 --learning-rate 1e-4 --weight-decay 0.01 --job-dir "/mnt/ViewFormer/sm7-transformer-training" --pose-multiplier 0.2"
