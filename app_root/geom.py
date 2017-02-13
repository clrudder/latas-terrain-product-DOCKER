#!/usr/bin/env python
# encoding=utf8

#############################################################################################
#
#  geom.py
#
#  Created by: Matthew Winchester, Charles Rudder
#              PrecisionHawk
#
#  Version 0.1: Oct 21, 2016
#               - Used to find intersections in GBDX shape files.
#
#  Usage:python geom.py
#
#   Requirements: wcs.py
#############################################################################################


import fnmatch
import os
from shapely.wkb import loads
from shapely.geometry import *
import fiona
from osgeo import ogr
from wcs import *


def get_intersection(poly1_path, poly2_path):
	#create placeholder polygons
    one = Polygon()
    two = Polygon()
	#open shapefiles and set as layers
    shp1 = ogr.Open(poly1_path)
    shp2 = ogr.Open(poly2_path)
    layer1 = shp1.GetLayer()
    layer2 = shp2.GetLayer()
	# write all polygons to placeholder polys
    for element in layer1:
        geom = loads(element.GetGeometryRef().ExportToWkb())
        one = one.union(geom)
    for element in layer2:
        geom = loads(element.GetGeometryRef().ExportToWkb())
        two = two.union(geom)
    #return intersected placeholder polys and get extent
    return one.intersection(two).bounds

def wcs_rows_cols(coords, res=0.00027777778):
    '''returns cols and rows for wcs getcoverage
        default is to handle 1/3 arc second resolution
    '''
    minX = coords[0]
    minY = coords[1]
    maxX = coords[2]
    maxY = coords[3]
    cols = (maxX - minX)/res
    rows = (maxY - minY)/res
    return str(cols) + ',' + str(rows)
    
#Grabs the WKT Polygon of a list of shape files
def get_shapes(shapefile_list):
    shapes = []
    for shape_path in shapefile_list:
        with fiona.open(shape_path) as src:
            shapes.append(src[0]['geometry']['coordinates'][0])
            src.close()
    return shapes

#Gets projections of shape files
def get_proj(shapefile_list):
    projs = []
    for shape_path in shapefile_list:
        with fiona.open(shape_path) as src:
            projs.append(src.crs)
            src.close()
    return projs

#Test if a list of projection elements are all the same. 
def test_projs(proj_list):
    if isinstance(proj_list, list): 
        return all(x == proj_list[0] for x in proj_list)
    else:
        return False

#Grab strip shapes
def find_shapefiles(folder):
    shapes = []
    for r,d,f in os.walk(folder):
        for file in fnmatch.filter(f, "*STRIP_SHAPE.shp"):  
            shapes.append(os.path.join(r, file))
    return shapes


    
if __name__ == "__main__":

    target = '/Users/mwinchester/AU-dataset'

    paths = find_shapefiles(target)

    print paths

    area = get_intersection(paths[0], paths[1])

    print "Area: ", area
    coor = []
    for a in area:
        coor.append(a)

    print coor

    p = get_proj(paths)
    print p[0]

    if test_projs(p):
        print "all projections the same"
    else:
        print "multiple projections detected", p

    #get_coverage("PH-ELEV", coor, "/Users/mwinchester") 
    size = wcs_rows_cols(coor)

    print "COOR: ", coor
    print "SIZE: ", size

    ret = export_image(coor, path="/Users/mwinchester", crs="4326", gridoff=size)

    print "RET: ", ret

