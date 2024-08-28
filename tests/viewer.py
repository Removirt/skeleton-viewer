from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import cloudvolume
from cloudvolume import Skeleton
import numpy as np
import nibabel as nib
def view(filename, port=8080):
    with open(filename, "rt") as swc:
        skel = Skeleton.from_swc(swc.read())

    data = nib.load('/home/lkipo/Codigo/removirt/Task08_HepaticVessel/Task08_HepaticVessel/labelsTr/hepaticvessel_001.nii.gz').get_fdata()
    fig, ax = skel.viewer()
    ax.voxels(data, edgecolor='k', alpha=0.5)
    # ax.voxels(data, edgecolor='k')
    plt.show()


if __name__=="__main__":
    view('/home/lkipo/Codigo/removirt/kimimaro_out/1.swc')
