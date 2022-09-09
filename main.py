from utils import load_img
from batch_process import *

img_root = '/Users/zyairelu/Desktop/Vessel_Segmentation/my_UNet/data/dop_img3/'
mask_root = '/Users/zyairelu/Desktop/Vessel_Segmentation/my_UNet/data/dop_img_mask3/'
saved_root = '/Users/zyairelu/Desktop/Vessel_Segmentation/my_UNet/data/grb3/'

re_img_root = '/Users/zyairelu/Desktop/Vessel_Segmentation/my_UNet/data/re_img/'
re_mask_root = '/Users/zyairelu/Desktop/Vessel_Segmentation/my_UNet/data/re_mask/'
re_saved_root = '/Users/zyairelu/Desktop/Vessel_Segmentation/my_UNet/data/grb_ud/'


# # batch process
# img_load = load_img(img_root)
# N = img_load.len_()
# for i in range(N):
#     batch_process(img_root, mask_root, i, saved_root)

# batch updated process
img_load = load_img(re_img_root)
N = img_load.len_()
for i in range(N):
    batch_process(re_img_root, re_mask_root, i, re_saved_root)
