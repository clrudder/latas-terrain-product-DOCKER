# -*- coding: utf-8 -*-
#############################################################################################
#  stitcher.py
#
#  Created by: Matt Winchester
#              PrecisionHawk
#
#  Version 0.1: November 15,2016
#               -Used to organize data for the ortho PCI stitching process call. 
#               
#############################################################################################

import os

#Finds all defined inputs in the mounted input directory.
#@Returns:      List        Contains paths to all input directories. 
def find_all_inputs(input_dir):

    #Gets around .DS_store and other directory artifacts
    dirs = []

    files = os.listdir(input_dir)

    print "files: ", files

    for f in files:
        r = os.path.join(input_dir, f)
        if os.path.isdir(r):
            dirs.append(r)

    return dirs

#Finds all .tif files in an data directory inside input directory
#@Returns       List        Paths to all tif files in a GBDX order
def get_tiff_inputs(data_input_directory):

    inputs = []

    for dirpath, dirnames, filenames in os.walk(data_input_directory):
        for filename in [f for f in filenames if f.endswith(".TIF")]:
            if "PAN" in dirpath:
                inputs.append(os.path.join(dirpath, filename))

    return inputs

#Builds the group files for all the inputs inside a GBDX task
#@Returns       List        Paths to all group{x}.txt files
#@Produces      Files       Group files for each gbdx order (PAN).
def build_group_files(input_dir, stitch_dir):

    group_dict = {}
    g_count = 0

    input_dirs = find_all_inputs(input_dir)

    print "input_dirs: ", input_dirs

    #For each input directory, find all the tiffs and write to group{x}.txt file
    for dir in input_dirs:
        g_count += 1
        print g_count

        #grab name of order from directory
        orderdir = find_all_inputs(dir)[0]
        head, ordername = os.path.split(orderdir)
        #Right Split name from file type
        ordernum = ordername.rsplit('_', 2)[0]

        print "ordernum: ", ordernum

        #build group file for input, ie: 055bleh.pix 
        stitchFile = os.path.join(stitch_dir, ordernum) + ".pix"
        print "Stitchfile: ", stitchFile
        
        #Collect all input for the group

        inputs = get_tiff_inputs(dir)
        
        g_path = os.path.join(stitch_dir, "group{}.txt".format(g_count))
        mfile = open(g_path, "w")
        print "G PATH : ", g_path

        for file in sorted(inputs):
            mfile.write(file + "\n")
            print "FILE TO WRITE : ", file

        #append group path to groups 
        group_dict[g_path] = stitchFile

        mfile.close()

    return group_dict


if __name__ == "__main__":

    inputdir = "/Users/mwinchester/AU-dataset"
    output = "/Users/mwinchester/Desktop/"
    stitch_d = os.path.join(output, "stitched")

    groups = build_group_files(inputdir, stitch_d)

    print "Groups: ", groups

