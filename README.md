# ViewFormer

Hello. 
This is an edit of the ViewFormer paper: https://github.com/jkulhanek/viewformer

To install requirment, just run the following command:
pip install -e .


Original paper results:
mse: 41.745335
    rmse: 6.111624
    mae: 1.500933
    psnr: 32.927101
    lpips: 0.027030
    ssim: 0.973110
Codebook training
|           |    mse    |   rmse   |     mae   |    psnr   |   lpips   |   ssim   |
| --------- | --------- | -------- | --------- | --------- | --------- | ---------|
| paper     | 40.111782 | 6.122104 | 1.783276  | 32.679970 | 0.033483  | 0.962444 |
| trained   | 41.745335 | 6.111624 | 1.500933  | 32.927101 | 0.027030  | 0.973110 |
