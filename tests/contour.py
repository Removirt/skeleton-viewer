import numpy as np
import nibabel as nib
import cv2 as cv
import matplotlib.pyplot as plt

ann = nib.load('/home/lkipo/Codigo/removirt/Task08_HepaticVessel/Task08_HepaticVessel/labelsTr/hepaticvessel_001.nii.gz').get_fdata()
print(ann.shape)

contours = []

for i in range(ann.shape[-1]):
    img = ann[:,:,i]
    # img_cv = cv.imread(img)
    # img = (img>1).astype(np.uint8)
    img2 = img.astype(np.float32)
    img2 = cv.cvtColor(img2, cv.COLOR_GRAY2BGR)
    # contour = cv.findContours(img, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
    # contours.append(contour[0][0][0][0])
    # cv.drawContours(img2, contour, -1, (0, 255, 0), 3)
    # if contour[1] is not None:
    #     print(contour)
    #     break
    # plt.scatter(contour[:,0], contour[:,1])
    plt.imshow(img)
    plt.show()
# print(contours[0])


plt.scatter