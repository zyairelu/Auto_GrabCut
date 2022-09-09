from utils import *
import os
import numpy as np
#from PIL import Image
import cv2
from core import GCClient

def batch_process(img_root, mask_root, index, saved_root):
# Automatically segment and save result
    img_loader = load_img(img_root)
    mask_loader = load_img(mask_root)

    img, img_name = img_loader.get_img(index)
    mask, _ = mask_loader.get_img(index)   # the output of load_img is PIL format
    # print(np.sum(np.array(mask)==255))
    mask_sc = img_scour(mask)
    rect = draw_box(mask_sc)


    '''grabCut body'''
    component_count = 5

    # translate to array from PIL
    img = np.array(img)
    mask = np.array(mask)
    # init output
    output = np.zeros(img.shape, np.uint8)
    # init GCClient
    GC = GCClient(img, component_count)
    # assign rect
    GC._rect = rect
    GC._mask[GC._rect[1]+GC._thickness:GC._rect[1]+GC._rect[3]-GC._thickness, GC._rect[0]+GC._thickness:GC._rect[0]+GC._rect[2]-GC._thickness] = GC._GC_PR_FGD
    ''' # Test first method
    # label mask
    f1 = 0
    f2 = 0 # flag for alternate labeling

    for i in range(20):
        labeled_l = random_label_ground(mask_sc)
        print(labeled_l)
        [x, y] = [labeled_l[0], labeled_l[1]]
        if labeled_l[2] == 0 and f1 == 0: # bg
            GC._DRAW_VAL = GC._DRAW_BG
            cv2.circle(GC._mask, (x, y), GC._thickness, GC._DRAW_VAL['val'], -1)
            f1 = 1
        elif labeled_l[2] == 0 and f1 == 1: # prob bg
            GC._DRAW_VAL = GC._DRAW_PR_BG
            cv2.circle(GC._mask, (x, y), GC._thickness, GC._DRAW_VAL['val'], -1)
            f1 = 0
        elif labeled_l[2] == 1 and f2 == 0: # fg
            GC._DRAW_VAL = GC._DRAW_FG
            cv2.circle(GC._mask, (x, y), GC._thickness, GC._DRAW_VAL['val'], -1)
            f2 = 1
        elif labeled_l[2] == 1 and f2 == 1: # prob bg
            GC._DRAW_VAL = GC._DRAW_PR_FG
            cv2.circle(GC._mask, (x, y), GC._thickness, GC._DRAW_VAL['val'], -1)
            f2 = 0
    '''
    for i in range(3): # bg and fg 
        labeled_0 = random_label_ground(mask_sc, 0)
        labeled_1 = random_label_ground(mask_sc, 1)
        print(labeled_0, labeled_1)
        [x0, y0] = [labeled_0[0], labeled_0[1]]
        [x1, y1] = [labeled_1[0], labeled_1[1]]
        GC._DRAW_VAL = GC._DRAW_BG
        cv2.circle(GC.img, (x0, y0), GC._thickness, GC._DRAW_VAL['color'], -1)
        cv2.circle(GC._mask, (x0, y0), GC._thickness, GC._DRAW_VAL['val'], -1)
        GC._DRAW_VAL = GC._DRAW_FG
        cv2.circle(GC.img, (x1, y1), GC._thickness, GC._DRAW_VAL['color'], -1)
        cv2.circle(GC._mask, (x1, y1), GC._thickness, GC._DRAW_VAL['val'], -1)
    for j in range(3): # prob bg and fg 
        labeled_0 = random_label_ground(mask_sc, 0)
        labeled_1 = random_label_ground(mask_sc, 1)
        print(labeled_0, labeled_1)
        [x0, y0] = [labeled_0[0], labeled_0[1]]
        [x1, y1] = [labeled_1[0], labeled_1[1]]
        GC._DRAW_VAL = GC._DRAW_PR_BG
        cv2.circle(GC.img, (x0, y0), GC._thickness, GC._DRAW_VAL['color'], -1)
        cv2.circle(GC._mask, (x0, y0), GC._thickness, GC._DRAW_VAL['val'], -1)
        GC._DRAW_VAL = GC._DRAW_PR_FG
        cv2.circle(GC.img, (x1, y1), GC._thickness, GC._DRAW_VAL['color'], -1)
        cv2.circle(GC._mask, (x1, y1), GC._thickness, GC._DRAW_VAL['val'], -1)

    # run grabCut
    # GC._mask = Image.fromarray(GC._mask)
    # GC._mask.show()
    # print(np.sum(np.array(GC._mask)==0))

    # cv2.namedWindow('img')
    # cv2.imshow('img', GC.img)
    # cv2.waitKey(0)

    GC.run()
    GC.iter(1)
    FGD = np.where((GC._mask == 1) + (GC._mask == 3), 255, 0).astype('uint8')
    output = cv2.bitwise_and(GC.img2, GC.img2, mask = FGD)
    # output = Image.fromarray(output)
    # output.show()

    # save section
    saved_path = os.path.join(saved_root + img_name[:-4] + '_gc.jpg')
    cv2.imwrite(saved_path, output)
    print("Result saved as image %s_gc.jpg"%(img_name[:-4]))