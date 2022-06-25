#!/bin/bash
#SBATCH -J code_gen
#SBATCH -o %x.%j.out
#SBATCH -e %x.%j.err
#SBATCH -G 1
#SBATCH --nodes 1

# You can start a container on each node from a shared squashfs file
srun --mpi=pmix --gpus=1 --container-image=/users/rosenbaum/aheidar/containers/tensorflow:21.07-tf2-py3.sqsh --container-save=/users/rosenbaum/aheidar/containers/tensorflow:21.07-tf2-py3.sqsh --container-mounts=/users/rosenbaum/aheidar/code/ViewFormer:/mnt/ViewFormer -w dgx01 --pty /bin/bash -c "python /mnt/ViewFormer/viewformer/cli.py generate-codes --model /mnt/ViewFormer/sm7-codebook-v3/last.ckpt --dataset /mnt/ViewFormer/datasets/sm7/ --output /mnt/ViewFormer/sm7-code-represenation --batch-size 64"
