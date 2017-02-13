#!/usr/bin/env python
# encoding=utf8

#############################################################################################
#
#  genDSM.py
#
#  Created by: Matthew Winchester
#              PrecisionHawk
#  Modified by: Charles Rudder
#				PrecisionHawk
#
#  Version 0.3: January 3, 2017
#               -Wrapper to DSM_from_Stereo.py/proc_dsm.py, used in a docker container on gbdx
#  Usage: python genDSM.py /path1/ /path2/ /path3/
#               
#############################################################################################

import os
import sys
import DSM_from_Stereo as dsm
import geom
import wcs

def usage():
    print "Usage: {} /path/to/stereopair/folder /path/to/output/folder /path/to/temp/folder".format(sys.argv[0])
    print "Example: {} /home/data/stereo/001 /home/data/srtmdir /home/dsm/output".format(sys.argv[0])
    sys.exit(2)


#Calls the DSM processing code and return results on the stack
def process(inputdir, outputdir, tmp_dir):

    print "Loading output directory: {}...".format(outputdir)

    ######################
    # Build virtual dirs
    ######################

    if not os.path.exists(outputdir):
        os.mkdir(outputdir)
        print "output directory created"
    else:
        print "output directory already created. Assumption: mounted volume"
    print "output directory loaded"


    if not os.path.exists(tmp_dir):
        os.mkdir(tmp_dir)
        print "workspace directory created"
    else:
        print "workspace directory already created. Assumption: mounted volume"
    print "workspace directory loaded"


    print "collecting input shapes with path: ", inputdir
    inpaths = geom.find_shapefiles(inputdir)
    area = geom.get_intersection(inpaths[0], inpaths[1])
    coords = []
    for a in area:
        coords.append(a)
        
    size = geom.wcs_rows_cols(coords)
    #Get the geotiff to be delieved to the target SRTM directory
    print "Calling WCS server to generate SRTM cut on path: ", tmp_dir
    #srtm_path = wcs.get_coverage("SRTM", coords, path=tmp_dir)  #r"G:\SRTM\USGS_SRTM\Done\NorthAmerica_SRTM.tif" #
    srtm_path = wcs.export_image(coords, path=tmp_dir, crs="4326", gridoff=size)



    #Process DSM with new SRTM cut 
    results = dsm.main(inputdir, outputdir, srtm_path, tmp_dir)
    print "returning results through stack"
    return results


#Below i for processing command line inputs
if __name__ == "__main__":
    'variables for running locally'
#    directory = r'E:\DSM\Raleigh\0934111'
#    inputdir = os.path.join(directory,'pair')
#    outputdir = os.path.join(directory,'out')
#    tmp_dir = os.path.join(directory,'temp')
#    input_files = [inputdir, outputdir, tmp_dir]
    input_files=[]
    if len(sys.argv) == 4:
        input_files.append(str(sys.argv[1]))    # path to stereo pair folder 
        input_files.append(str(sys.argv[2]))    # path to output directory
        input_files.append(str(sys.argv[3]))    # path to SRTM
    else:
        usage()

    process(input_files[0], input_files[1], input_files[2])


