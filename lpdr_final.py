# -*- coding: utf-8 -*-
"""LPDR Final

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1B3CU5Nonv6RpxkdLpYxdTdZBfJn-DTBq
"""

from google.colab import drive
drive.mount('/content/gdrive')
wpod_net_path =  "/content/gdrive/MyDrive/411project/Plate_detect_and_recognize-master/Plate_detect_and_recognize-master/wpod-net.json"

import sys    
path_to_module = '/content/gdrive/MyDrive/411project/Plate_detect_and_recognize-master/Plate_detect_and_recognize-master/'
sys.path.append(path_to_module)
from local_utils import detect_lp

!pip install python_util
!pip install keras
!pip install paddlepaddle -i https://mirror.baidu.com/pypi/simple
!pip install "paddleocr>=2.0.1"

import cv2
import numpy as np
from google.colab.patches import cv2_imshow
import matplotlib.pyplot as plt
from os.path import splitext, basename
from keras.models import model_from_json
import glob
from google.colab.patches import cv2_imshow

from paddleocr import PaddleOCR,draw_ocr
def load_model(path):
    try:
        path = splitext(path)[0]
        with open('%s.json' % path, 'r') as json_file:
            model_json = json_file.read()
        model = model_from_json(model_json, custom_objects={})
        model.load_weights('%s.h5' % path)
        print("Loading model successfully...")
        return model
    except Exception as e:
        print(e)

wpod_net = load_model(wpod_net_path)

def preprocess_image(image_path,resize=False):
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    plt.imshow(img)
    plt.show()
    img = img / 255
    if resize:
        img = cv2.resize(img, (224,224))
    return img

image_paths = glob.glob("/content/gdrive/MyDrive/411project/Plate_detect_and_recognize-master/Plate_detect_and_recognize-master/test_img/*.jpg")
print("Found %i images..."%(len(image_paths)))

# Visualize data in subplot 
fig = plt.figure(figsize=(12,8))
cols = 1
rows = 1
fig_list = []
for i in range(cols*rows):
    fig_list.append(fig.add_subplot(rows,cols,i+1))
    title = splitext(basename(image_paths[i]))[0]
    fig_list[-1].set_title(title)
    img = preprocess_image(image_paths[i],True)
    plt.axis(False)
    plt.imshow(img)

plt.tight_layout(True)
plt.show()

from keras.utils.image_utils import save_img
def get_plate(image_path, Dmax=608, Dmin=256):
    vehicle = preprocess_image(image_path)
    ratio = float(max(vehicle.shape[:2])) / min(vehicle.shape[:2])
    side = int(ratio * Dmin)
    bound_dim = min(side, Dmax)
    _ , LpImg, _, cor = detect_lp(wpod_net, vehicle, bound_dim, lp_threshold=0.5)
    return LpImg, cor

# Obtain plate image and its coordinates from an image
test_image = image_paths[1]
LpImg,cor = get_plate(test_image)
print("Detect %i plate(s) in"%len(LpImg),splitext(basename(test_image))[0])
print("Coordinate of plate(s) in image: \n", cor)

# Visualize our result
plt.figure(figsize=(10,5))
plt.subplot(1,2,1)
plt.axis(False)
plt.imshow(preprocess_image(test_image))
plt.subplot(1,2,2)
plt.axis(False)
plt.imshow(LpImg[0])
save_img('/content/gdrive/MyDrive/411project/trocr/augmentation/images/test.jpg', LpImg[0])

def calculate_rectangle(box):
  topleftx, toplefty = box[0]
  toprightx, toprighty = box[1]
  btmleftx, btmlefty = box[3]
  btmrightx, btmrighty = box[2]
  rectangle = (toprightx - topleftx) * (btmlefty - toplefty)
  return rectangle, int(topleftx), int(toplefty), int(btmrightx), int(btmrighty)

ocr = PaddleOCR(use_angle_cls=True, lang='en') # need to run only once to download and load model into memory
img_path = '/content/gdrive/MyDrive/411project/trocr/augmentation/images/test.jpg'
img=cv2.imread(img_path)
result = ocr.ocr(img, cls=True)
for idx in range(len(result)):
    res = result[idx]
    # for line in res:
    #     #print(line)


# draw result
from PIL import Image
result = result[0]

image = Image.open(img_path).convert('RGB')
boxes = [line[0] for line in result]
txts = [line[1][0] for line in result]
scores = [line[1][1] for line in result]
# im_show = draw_ocr(image, boxes, txts, scores)
# im_show = Image.fromarray(im_show)
# im_show.save('result.jpg')

rectangles = []
coords = []
i = 0;
for box in boxes:
  area, lx, ly, rx, ry = calculate_rectangle(box)
  rectangles.append([area, txts[i], i])
  coords.append([[lx, ly], [rx, ry]])
  i += 1

rectangles.sort(key=lambda row: (row[0]), reverse=True)
detected_text = rectangles[0][1]
result = cv2.rectangle(img, coords[rectangles[0][2]][0], coords[rectangles[0][2]][1],(255, 0, 0), 4)
cv2.putText(result, detected_text, coords[rectangles[0][2]][0], cv2.FONT_HERSHEY_SIMPLEX, .9, (0, 0, 255), 2)
cv2_imshow(result)