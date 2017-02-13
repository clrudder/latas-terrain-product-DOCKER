# -*- coding: utf-8 -*-
#############################################################################################
#  DSM_from_Stereo.py
#
#  Created by: Charles Rudder, Matt Winchester
#              PrecisionHawk
#
#  Version 1: September 21,2016
#               -Convertes stereo pair satellite imagery into Digital Surface model
#  Usage: python DSM_from_Stereo.py /path/to/srtm/folder /home/data/srtm/srtm.tif
#               
#############################################################################################
import os, sys, traceback
import logging
import time
import utm
import shutil
import DSM_utils
#import platform
import pci.nspio
from pci.stitch import stitch as stitch
from pci.link import link as link
from pci.pyramid import pyramid as pyramid
from pci.exceptions import PCIException
from pci.crproj import crproj as crproj
from pci.autotie import autotie as autotie
from pci.tprefn import tprefn as tprefn
from pci.cpmmseg import cpmmseg as cpmmseg
from pci.oemodel import oemodel as oemodel
from pci.epipolar import epipolar as epipolar
from pci.autodem import autodem as autodem
#from pci.api import datasource as ds
#from pci.fsharp import fsharp
#from pci.fme import fme
from pci.fexport import fexport as fexport
from jsonWriter import jsonWriter
import stitcher


#Create global for scope reasons
jw = jsonWriter("")

logger = logging.getLogger(__name__)
   
def usage():
    print "Usage: {} /new/output/directory /path/to/stereopair/folder /path/to/srtm/folder".format(sys.argv[0])
    print "Example: {} /home/data/out /home/data/stereo/001 /home/data/srtm".format(sys.argv[0])
    sys.exit(2)


#Requires output, input directories and an srtm path
def main(input_dir, out_dir, srtm_path, tmp_dir):
    start = time.time()
    
    DOCKEr_GDW_PATH = 'gdalwarp'
    print "DOCKEr_GDW_PATH: ", DOCKEr_GDW_PATH

    #Initialize GBDX logger
    global jw
    jw = jsonWriter(out_dir)
    print "created status.json file"

    #Initalize PCI log file
    setup_log(out_dir)
    register_logger()
    
    print "created logger"

    pci.nspio.Logger.logEvent('Starting Stereoscopic DSM creation...')
    
    try:
        ## build folder structure to correctly assign output     
        internal_folders = DSM_utils.build_folder_structure(tmp_dir)
        img_dir = internal_folders[0]
        epipolar_dir = internal_folders[1]
        epi_dems_dir = internal_folders[2]
        dsm_dir = internal_folders[3]
        
        print "Begin processing data"
        
        # determine UTM projection to set up project
        shapefile_list = DSM_utils.find_shapefiles(input_dir)
        bbox = DSM_utils.shp_extent(shapefile_list[0])
        avg_Lat = (bbox[2] + bbox[3]) / 2.0
        avg_Lon = (bbox[0] + bbox[1]) / 2.0
        utm_code = utm.from_latlon(avg_Lat, avg_Lon)
        
        # determine orientation of satellite imagery to follow STITCH workflow or process
            # individual image tiles separately
        orientations = []
        for shapefile in shapefile_list:
            direction = DSM_utils.orientation(shapefile)
            orientations.append(direction)
            
        if 'EW' in orientations:
            print "Satellite collection oriented East-West...processing individual image tiles."
            print "Link TIF files as PIX files"
            pci.nspio.Logger.logEvent('Linking image tiles as PIX for inclusion in project...')
            input_image_tiles = get_tiff_inputs(input_dir)
        
            if len(input_image_tiles) > 0:
                for tif in input_image_tiles:
                    link_filename = os.path.splitext(os.path.basename(tif))[0] + '_LINK.pix'
                    link_file = os.path.join(img_dir, link_filename)
                    
                    try:
                        link(tif, link_file, [])
                        pyramid(link_file, [], "YES", [-2], "NEAR")
                        print "link file created here: ", link_file
                    except PCIException, e:
                        print "PCI Exception"
                        print e
                        print e.__doc__
                        print e.message
                    except Exception, e:
                        print e.__doc__
                        print e.message
                        print e
        else:
            print "Satellite collection oriented North-South...stitching tiles into strips."
            print "Begin stitching tiles"
            group_dict = stitcher.build_group_files(input_dir, img_dir)
            pci.nspio.Logger.logEvent("Group files constructed")
            #Debug
            print "GROUP DICT : ", group_dict
            print "Group files built. Constructing stitched strips"
            #Iterate through groups and stitch the tiles to the file stitch
            for group, stitchFile in group_dict.iteritems():
                if os.path.exists(stitchFile):
                    os.remove(stitchFile)
                pci.nspio.Logger.logEvent("Group: {}, Stitch: {}".format(group, stitchFile))
                stitch_strips(group, stitchFile)
                
        ## Create OrthoEngine project file to store project data
        img_files = os.path.join(img_dir, "*.pix")
        oeproj = os.path.join(tmp_dir, "oe_initial.prj")
        dem = srtm_path    
        
        mapunits = 'UTM {} {} D000'.format(str(utm_code[2]), utm_code[3])
        crproj(img_files, [], oeproj, "RFIA", mapunits )
    
        ##  Run Automatic Tie Point Collection and refine to save only acceptable
            ##      tie points with low RMSE
        print "Calculate Tie points"
        tp_oeproj = os.path.join(tmp_dir, "output_oetp.prj")
        if os.path.exists(tp_oeproj):
            os.remove(tp_oeproj)
        get_tie(oeproj, tp_oeproj, dem)
    
        ## Generate the epipolar images, which are used to triangulate the 3D 
        ##   coordinates for the DEM
        print "Generate epipolars"
        epi_images(img_dir, epipolar_dir)
        if not os.listdir(epipolar_dir):
                raise Exception("Epipolar Images not created, tie point creation likely to blame")
                
        ## Automatically extract a Digital Surface Model from satellite stereo pairs
        ##      proceeds to build epipolar DSMs then an output geocoded DSM
        dsm_name = DSM_utils.filename_from_orderID(input_dir) + ".pix"
        geocoded_dsm_pix = os.path.join(dsm_dir, dsm_name)
        geocoded_dsm_tif = os.path.join(dsm_dir, dsm_name[:-4] + '.TIF')
        final_dsm_tif = os.path.join(out_dir, dsm_name[:-4] + '_FINAL.TIF')
        dem_res = [2, 2]
    
        print "process epipolars to dem"
    
        epi_to_dem(epipolar_dir, epi_dems_dir, geocoded_dsm_pix, mapunits, dem_res)
    
        ## Filter output DSM with Median filter to smooth output, 
        ##  followed by edge sharpening filter
        ##  followed by export to TIF.
        refine_filters(geocoded_dsm_pix, geocoded_dsm_tif)
        innerClip(input_dir, geocoded_dsm_tif, final_dsm_tif, DOCKEr_GDW_PATH)
    
        pci.nspio.Logger.logEvent("DSM successfully created!")
        pci.nspio.Logger.logEvent("Cleaning up temp directory and input data folder")
    #    shutil.rmtree(tmp_dir)
    #    shutil.rmtree(input_dir)
        pci.nspio.Logger.logEvent("Processing Time: {} minutes".format(str((time.time() - start)/60.0)))
       
        print "total time taken (seconds): ", str(time.time() - start)
        return "Success! DSM created!"
    
    except Exception, e:
        pci.nspio.Logger.logEvent(e)
        jw.failure(e)
        sys.exit(0)

###############################################################################
def log_messages(msg, file = 'NSPIO', line = -1):
    logger.info(msg)    

def setup_log(topLevelDir):
    #create logging file
    LOG_FILENAME = os.path.join(topLevelDir,'DSM_fromStereo.log')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(LOG_FILENAME)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
def register_logger():    
    pci.nspio.Logger.clear()
    pci.nspio.Report.clear()
    pci.nspio.PCIWarning.clear()
    pci.nspio.Debugger.clear()
    pci.nspio.Logger.registerInstance(log_messages)
    pci.nspio.PCIWarning.registerInstance(log_messages)
    pci.nspio.Debugger.registerInstance(log_messages)
    pci.nspio.Report.registerInstance(log_messages)


def stitch_strips(in_files, stitched):

    print "ENTERING STITCH FUNCTION"

    #pci.nspio.Logger.logEvent('Stitching ' + os.path.basename(in_files) + 'files to combine RPC information.')

    print "stitching images"
    try:
        stitch(in_files, stitched)
        pyramid(stitched, [], "YES", [-2], "NEAR")
        #pci.nspio.Logger.logEvent('Stitching ' + stitched + ' complete')    

    except Exception, e:
        #Print everything Matthew, reveal the truth...
        error = ""
        error += "params: {} {} \n".format(in_files, stitched)
        error += str(sys.exc_info())
        error += "\n"
        error += str(traceback.format_exc())
        error += "\n"
        #pci.nspio.Logger.logEvent(error)
        pci.nspio.Logger.logEvent(e)
        print error
        jw.failure("stitch_strips crapped out")
        sys.exit(0)
    
    return stitched


def get_tie(oeproj, tp_oeproj, dem):
    pci.nspio.Logger.logEvent('Collecting Tie Points')
    try:
        tie = autotie(oeproj, tp_oeproj,  "ALL",  "REPLACE", 
                      [],  dem, [1],  [-32767], "", "",  [], 
                      "GRID:64",  "ENTIRE",  "FFTP", [200], 
                      "PIXEL",  [0.75],  "")
        pci.nspio.Logger.logEvent('Refining Tie Points...')
        
        # Run automatic Tie Point Refinement
        reject = [5, 2.0, 2.0]
        tprefn(tp_oeproj, reject, "")
        
        #Copy Math Model out to file and run bundle adjustment
        cpmmseg(tp_oeproj, "", [])
        oemodel(tp_oeproj, "")
        pci.nspio.Logger.logEvent('Collecting Tie Points Complete')
    
    except Exception, e:
        #Print everything Matthew, reveal the truth...
        error = ""
        error += str(sys.exc_info())
        error += "\n"
        error += str(traceback.format_exc())
        error +="\n"
        pci.nspio.Logger.logEvent(error)
        pci.nspio.Logger.logEvent(e)
        print error
        jw.failure("get tie crapped out")
        sys.exit(0)
    
    return(tie)


def epi_images(img_dir, epiImages_dir):
    pci.nspio.Logger.logEvent('Creating Epipolar Images')
    try:
        mfile = os.path.join(img_dir, "*.pix")
        epi_img = epipolar(mfile, [], [], [], 
                             "0", "ALL", [5], 
                             [1], epiImages_dir, 
                             [-9999], "", "", [])
        print "EPIPOLAR IMAGE CREATION COMPLETE"
        #pci.nspio.Logger.logEvent('Epipolar image creation Complete')
        
    except PCIException, e:
        #pci.nspio.Logger.logEvent(str(e))
        err = "Epipolar image creation failed. Try again..."
        print err
        #pci.nspio.Logger.logEvent(err)
        jw.failure(err)
        sys.exit(0)  
    
    return(epi_img)

def epi_to_dem(epiImages_dir, epiDems_dir, geocoded_dsm, mapunits, dem_res):
    pci.nspio.Logger.logEvent('Creating DSM from stereo images')
    try:
        dsm = autodem(epiImages_dir, [], [], [], 
                    		[-1000], [-9999], 
                    		"HIGH", "HILLY", "16S", [], "YES", 
                    		"YES", "NO", "", epiDems_dir, geocoded_dsm, 
                              "", "", [], [], dem_res, "SCORE")
        pci.nspio.Logger.logEvent('DSM from stereo Complete')
        
    except PCIException, e:
        pci.nspio.Logger.logEvent(str(e))
        err = "DSM from stereo failed. Try again..."
        pci.nspio.Logger.logEvent(err)
        jw.failure(err)
        sys.exit(0)
        
    return(dsm)        

def refine_filters(geocoded_dsm, geocoded_dsm_tif):
    pci.nspio.Logger.logEvent('DSM refinement started')
    try:
        #refine = fme(geocoded_dsm, [1], [1], [7,7], [], [-9999], [-1000], "")
        #refine = fsharp(geocoded_dsm, [1], [1], [7,7], [], "")
        refine = fexport(geocoded_dsm, geocoded_dsm_tif, [],[1],[],[],[],[], "TIF")
        refine = DSM_utils.setNoData(geocoded_dsm_tif, -9999)
        pci.nspio.Logger.logEvent('Refinement Complete')
        
    except PCIException, e:
        pci.nspio.Logger.logEvent(str(e))
        err = "Refining filters failed. Try again..."
        pci.nspio.Logger.logEvent(err)
        jw.failure(err)
        sys.exit(0)
    
    return(refine)

    
def innerClip(directory, input_dsm, output_dsm, DOCKER_GDW_PATH):
    pci.nspio.Logger.logEvent('Clipping outer rim of DSM to remove interpolated data')
    try:
        # create intersection shapefile and create negative buffer to clip away ring of data
        stripShape = DSM_utils.find_shapefiles(directory)
        projection = DSM_utils.read_projection(input_dsm)
        intersectSHP = DSM_utils.intersection(stripShape[0], stripShape[1], projection, os.path.dirname(input_dsm))
        output_dir = os.path.dirname(output_dsm)
        buff_fn = DSM_utils.filename_from_orderID(directory) + "_DataBound.shp"
        bufferSHP = DSM_utils.createBuffer(intersectSHP, os.path.join(output_dir, buff_fn), -150)
        
        # run GDALWARP to remove anomalous data at intersected edges, update noData value, and adjust extent
        os.system('gdalwarp -cutline "{0}" -crop_to_cutline -multi -dstnodata 0.0 "{1}" "{2}" '.format(bufferSHP, input_dsm, output_dsm))

        pci.nspio.Logger.logEvent('DSM clipped to remove interpolated data')
    except PCIException, e:
        pci.nspio.Logger.logEvent(str(e))
        err = "Clip failed"
        pci.nspio.Logger.logEvent(err)
        jw.failure(err)
        sys.exit(0)    
    

#Finds all defined inputs in the mounted input directory.
#@Returns:      List        Contains paths to all input directories. 
def find_all_inputs(input_dir):

    #Gets around .DS_store and other directory artifacts
    dirs = []

    files = os.listdir(input_dir)

    e = "for directory" + input_dir + " files found: " + files
    print e
    pci.nspio.Logger.logEvent(e)

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
        g = "G PATH : ", g_path
        pci.nspio.Logger.logEvent(g)
        print g

        for file in sorted(inputs):
            mfile.write(file + "\n")
            e = "FILE TO WRITE : ", file
            pci.nspio.Logger.logEvent(e)
            print e

        #append group path to groups 
        group_dict[g_path] = stitchFile

        mfile.close()

    return group_dict




if __name__ == '__main__':

    start = time.time()
    #Process standard input

    #input_files = [r'O:\DSM_WORKSPACE\LATAS_API_PriotiesData\3DR\104306', r"O:\SRTM\USGS_SRTM\Done\NorthAmerica_SRTM.tif"]

    #Pass input params to main
    if (len(sys.argv) == 4):
        inputdir   = str(sys.argv[1])
        outputdir    = str(sys.argv[2])
        srtm_path    = str(sys.argv[3])
        main(inputdir, outputdir, srtm_path)
        print("%f minutes" % ((time.time() - start)/60) )
    else:
        usage()


