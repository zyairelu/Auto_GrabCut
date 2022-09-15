import os
from PIL import Image
import numpy as np
import random

class load_img(object):
    def __init__(self, root):
        self.root = root
        self.img_name_list = os.listdir(self.root)
        self.img_num = len(self.img_name_list)

    def get_img(self, index):
        img_path = self.root + self.img_name_list[index]
        image = Image.open(img_path)
        return image, self.img_name_list[index]
    
    def len_(self):
        return len(self.img_name_list)

    # def get_single_img(self, s_path):
    #     image = Image.open(s_path)
    #     return image
    

def img_scour(mask):
    img_size = mask.size
    mask = np.array(mask)
    # for i in range(0, img_size[0]):
    #     for j in range(0, img_size[1]):
    #         if mask[i, j] < 128:
    #             mask[i, j] = 0
    #         else:
    #             mask[i, j] = 255
    return Image.fromarray(mask)


def draw_box(mask):
    img_size = mask.size
    mask = np.array(mask)
    for i in range(0, img_size[0]):
        if 255 in mask[:,i]:
            x1 = i
            break
    for i in range(img_size[0]-1, 0, -1):
        if 255 in mask[:,i]:
            x2 = i
            break
    for i in range(0, img_size[1]):
        if 255 in mask[i,:]:
            y1 = i
            break
    for i in range(img_size[1]-1, 0, -1):
        if 255 in mask[i,:]:
            y2 = i
            break
    width = x2 - x1
    height = y2 - y1
    return [x1, y1, width, height]

# def random_label_ground(mask_s):
#     mask_s = np.array(mask_s)
#     x = random.randint(0, 99)
#     y = random.randint(0, 99)
#     if mask_s[x, y] == 0:
#         mask_flag = 0  # background
#     else:
#         mask_flag = 1  # foreground
#     return [x, y, mask_flag]

def random_label_ground(mask_s, flag):
    '''flag -> 0: bg;    flag -> 1: fg'''
    mask_s = np.array(mask_s)
    index_0 = np.where(mask_s == 0)
    # index_255 = np.where(mask_s == 255)
    index_255 = np.where(mask_s != 0)
    index_0 = np.array(index_0)
    index_255 = np.array(index_255)
    if flag == 0:
        # row_0 = random.randint(0, np.size(index_0, 0))
        col_0 = random.randint(0, np.size(index_0, 1)-1)
        [x, y] = index_0[:, col_0]
        # [x, y] = [index_0[0, col_0], index_0[1, col_0]]
        return [x, y]
    elif flag == 1:
        # row_1 = random.randint(0, np.size(index_255, 0))
        col_1 = random.randint(0, np.size(index_255, 1)-1)
        [x, y] = index_255[:, col_1]
        # [x, y] = [index_255[0, col_1], index_255[1, col_1]]
        return [x, y]

def judgment(img):
    # Determine whether the processed image is qualified
    img = np.array(img)
    EA_mat = np.where(img != 0)

    TH = 600     # threshold
    Bad_Points = np.size(EA_mat, 1)

    if Bad_Points < TH:
        print('This image is bad!')
        return False
    else:
        return True