#!/bin/bash
#SBATCH -J t_eval
#SBATCH -o %x.%j.out
#SBATCH -e %x.%j.err
#SBATCH -G 1
#SBATCH --nodes 1
# You can start a container on each node from a shared squashfs file 
srun --mpi=pmix --gpus=1 --container-image=/users/rosenbaum/aheidar/containers/tensorflow:21.07-tf2-py3.sqsh --container-save=/users/rosenbaum/aheidar/containers/tensorflow:21.07-tf2-py3.sqsh --container-mounts=/users/rosenbaum/aheidar/code/ViewFormer:/mnt/ViewFormer --pty /bin/bash -c "python /mnt/ViewFormer/viewformer/cli.py evaluate transformer --codebook-model "/mnt/ViewFormer/sm7-codebook-v5/last.ckpt" --transformer-model "/mnt/ViewFormer/sm7-transformer-training/weights.model.099-last" --loader-path "/mnt/ViewFormer/datasets/sm7" --loader dataset --loader-split test --batch-size 1 --image-size 128 --num-eval-images 1000 --job-dir "/mnt/ViewFormer/sm7-transformer-evaluation-v5" "
