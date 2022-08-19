#!/bin/bash
#SBATCH -J transformer-loc
#SBATCH -o %x.%j.out
#SBATCH -e %x.%j.err
#SBATCH -G 8
#SBATCH --nodes 1

# You can start a container on each node from a shared squashfs file
srun --mpi=pmix --gpus=8 --container-image=/users/rosenbaum/aheidar/containers/tensorflow:21.07-tf2-py3.sqsh --container-save=/users/rosenbaum/aheidar/containers/tensorflow:21.07-tf2-py3.sqsh --container-mounts=/users/rosenbaum/aheidar/code/ViewFormer:/mnt/ViewFormer -w dgx02 --pty /bin/bash -c "python /mnt/ViewFormer/viewformer/cli.py train transformer --dataset '/mnt/ViewFormer/code_representations/sm7-code-represenation-v5' --codebook-model '/mnt/ViewFormer/trainings/sm7-codebook-v5/last.ckpt' --sequence-size 6 --n-loss-skip 1 --batch-size 128 --fp16 --total-steps 1200000 --localization-weight 'cosine(0,1,120000)' --learning-rate 1e-4 --weight-decay 0.01 --job-dir '/mnt/ViewFormer/trainings/sm7-transformer-training-v5-with-loc' --pose-multiplier 0.2 --wandb --wandb-exp-name 'V5-with-localization' --wandb-proj-name 'train_transformer_sm7'"
