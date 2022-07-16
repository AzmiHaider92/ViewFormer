# ViewFormer

Hello. 
This is an edit of the ViewFormer paper: https://github.com/jkulhanek/viewformer

To install requirment, just run the following command:
pip install -e .


- codebook and transformer were trained with the parameters given by the original project and achieved the following results.

Codebook training
|         |    mse    |   rmse   |     mae   |    psnr   |   lpips   |   ssim   |
| ------- | --------- | -------- | --------- | --------- | --------- | ---------|
| paper   | 40.111782 | 6.122104 | 1.783276  | 32.679970 | 0.033483  | 0.962444 |
| trained | 41.745335 | 6.111624 | 1.500933  | 32.927101 | 0.027030  | 0.973110 |


Transformer training: 
|         |  loc-angle  | loc-angle-med |  loc-dist | loc-dist-med |    mse     |   rmse   |     mae   |    psnr   |   lpips   |   ssim   |
| ------- | ----------- | ------------- | --------- | ------------ | ---------- | -------- | --------- | --------- | --------- | -------- |
| paper   |  0.083059   |   0.067267    | 0.253630  |   0.210964   | 74.843483  | 8.186931 | 2.187041  | 30.247765 | 0.050506  | 0.949935 |
| trained |  0.186236   |   0.128448    | 0.496741  |   0.385123   | 105.547150 | 9.564821 | 2.301619  | 29.034624 | 0.041288  | 0.957995 |  
