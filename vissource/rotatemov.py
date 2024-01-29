# trace generated using paraview version 5.11.1-1745-ge8c78138a6
#import paraview
#paraview.compatibility.major = 5
#paraview.compatibility.minor = 11

import numpy as np
import math
import argparse
import os.path

#### import the simple module from the paraview
from paraview.simple import *
#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

parser = argparse.ArgumentParser(
                    prog='rotatemov',
                    description='Script to generate individual images for movie')
parser.add_argument('-d', '--datafile', help='path to the data file')
parser.add_argument('-c', '--connfile', help='path to the connectivity file')
args = parser.parse_args()

datafile = args.datafile
connfile = args.connfile
if not ( os.path.isfile(datafile) and os.path.isfile(connfile) ):
    print('Could not find the correct data and connectivity files')
    exit()

LoadPlugin("/home/local/KHQ/abhi.yenpure/repositories/eam/scripts/eam_reader.py", ns=globals())
LoadPlugin("/home/local/KHQ/abhi.yenpure/repositories/eam/scripts/eam_filters.py", ns=globals())
LoadPlugin("/home/local/KHQ/abhi.yenpure/repositories/eam/scripts/eam_projection.py", ns=globals())
LoadPlugin("/home/local/KHQ/abhi.yenpure/repositories/eam/scripts/eam_linesrc.py", ns=globals())

LoadState("/home/local/KHQ/abhi.yenpure/repositories/eam/forMovie/states/state_slice_lat_lev_rotate_layout_radar.pvsm")

# find source
data = FindSource('Data')
data.DataFile = datafile
data.ConnectivityFile = connfile
data.a2DVariables = ['CLDLOW', 'CLDTOT']
data.a3DMiddleLayerVariables = ['cnd01_ALST_ACTDIAG01', 'cnd01_AST_ACTDIAG01', 'cnd01_CDMC_ACTDIAG01', 'cnd01_CDNC_ACTDIAG01', 'cnd01_RAL_ACTDIAG01', 'cnd01_REL_ACTDIAG01']
data.UpdatePipeline()
SetActiveSource(data)
# Properties modified on v2_F2010_nc00_inst_macmic01eamh02010122500000nc

# find view
renderView1 = FindViewOrCreate('RenderView1', viewtype='RenderView')
renderView2 = FindViewOrCreate('RenderView2', viewtype='RenderView')

# get layout
layout1 = GetLayout()

# layout/tab size in pixels
layout1.SetSize(1970, 1144)

sin = math.sin
r   = math.radians
cos = math.cos

# find source
a2DDataCurtain  = FindSource('2DDataCurtain')
a2DRadarLine    = FindSource('2DRadarLine')
# set active source
#SetActiveSource(slice1)

# current camera placement for renderView2
renderView2.CameraPosition = [0.0, 0.0, 9275.129857372207]
renderView2.CameraFocalPoint = [0.0, 0.0, 0.510986328125]
renderView2.CameraParallelScale = 6378.5863535127

for i in range(1, 361): 
    # Properties modified on slice1.SliceType
    a2DDataCurtain.SliceType.Origin = [i, 78.25, 799.2482197458811]
    a2DRadarLine.longitude = i

    a = i
    # Clockwise rotation
    rZmatrix = np.array([[cos(r(a)), sin(r(a)), 0, 0],
                        [-sin(r(a)), cos(r(a)), 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]])
    ocam    = np.array([398.1654383050872, -3174.0890539452366, 2183.232066879151, 1.0])
    cam     = ocam.dot(rZmatrix)
    ofoc    = np.array([398.1654383050872, 0.0, 2183.232066879151, 1.0])
    foc     = ofoc.dot(rZmatrix)
    '''
    # current camera placement for renderView1
    renderView1.InteractionMode = '2D'
    renderView1.CameraPosition = [398.1654383050872, -3174.0890539452366, 2183.232066879151]
    renderView1.CameraFocalPoint = [398.1654383050872, 0.0, 2183.232066879151]
    renderView1.CameraViewUp = [0.0, 0.0, 1.0]
    '''
    renderView1.CameraPosition = [cam[0], cam[1], cam[2]]
    renderView1.CameraFocalPoint = [foc[0], foc[1], foc[2]]
    renderView1.CameraViewUp = [0.0, 0.0, 1.0]
    #renderView1.CameraParallelScale = 1386.1438050807299

    # update the view to ensure updated data information
    renderView1.Update()
    renderView2.Update()

    x = ('%04d' %i)
    filename = 'rotateZ' + x + '.png'
    print("Saving ", i)
    # save screenshot
    SaveScreenshot(filename, layout1, 16, SaveAllViews=1, ImageResolution=[1988, 1144])

