# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 16:15:58 2016

@author: Charles Rudder
USAGE: utility funcitons for DSM from Stereo pair 
"""
import os
import fnmatch
from shapely.wkb import loads
from shapely.geometry import *
import gdal
import osr
import ogr
import utm
import psutil
#import numpy as np
#from scipy.cluster.vq import kmeans, vq
#from scipy.ndimage.measurements import label
from pci.api import datasource as ds

    
def find_shapefiles(folder):
    shapes = []
    for r,d,f in os.walk(folder):
        for file in fnmatch.filter(f, "*STRIP_SHAPE.shp"):  
            shapes.append(os.path.join(r, file))
    return shapes

def orientation(shp):
    ds = ogr.Open(shp)  
    lyr = ds.GetLayer()
    minX, maxX, minY, maxY = lyr.GetExtent()
    lenX = abs(minX - maxX)
    lenY = abs(minY - maxY)
    if lenX > lenY:
        return 'EW'
    else:
        return 'NS'
        
def shp_extent(shapefile):
    ds = ogr.Open(shapefile)
    lyr = ds.GetLayer(0)
    extent = lyr.GetExtent()
    return extent 
    
def build_folder_structure(directory):
    folder_build = ['image_files','epipolar_images', 'epipolar_dems', 'dsm']

    internal_folders = []
    if not os.path.exists(directory):
        os.makedirs(directory)   
    for folder in folder_build:    
        dir = os.path.join(directory, folder)
        if not os.path.exists(dir):
            os.makedirs(dir) 
        internal_folders.append(dir)
    return internal_folders


def filename_from_orderID(folder):
    filename = ""

    dirs = os.listdir(folder)

    for dir in dirs:

        if os.path.isdir(os.path.join(folder, dir)):

            orders = os.listdir(os.path.join(folder,dir))

            file = fnmatch.filter(orders, '*.TXT')

            oname = file[0].split('_')[0]
            if filename == "":
                filename = oname
            else:
                filename += '_' + oname
                
    return filename

#def kmeans_segment(A, K=5):
#
#    A = A.astype('float32')
#    A = A[~np.isnan(A)].flatten()
#    size = A.shape[0]
#    samp_size = int(round(0.01 * size))
#    A_samp = np.random.choice(A,samp_size)
#    # K-means lableling
#    centers, _ = vq.kmeans(A_samp, K)
#    labels, _ = vq(A, centers)
#
#    break_mins = []
#    for i in range(K):
#        break_mins.append(np.min(A[labels==i]))
#    break_mins.sort()
#    break_mins.append(np.max(A))
#
#    return break_mins
                
def getNoData(input_rast):
    raster = gdal.Open(input_rast)
    band = raster.GetRasterBand(1)
    ndv = band.GetNoDataValue()
    return ndv

def get_3Q_memory():
    mem = psutil.virtual_memory()
    three_quarters = int(mem.total/(1048576)*(.75))
    return str(three_quarters)

def setNoData(input_rast, NDV):
    raster = gdal.Open(input_rast, gdal.GA_Update)
    raster.GetRasterBand(1).SetNoDataValue(NDV)
    raster.GetRasterBand(1).ComputeStatistics(False)
    raster = None

def read_projection(input_rast):
    raster = gdal.Open(input_rast)
    projection = raster.GetProjection()
    return projection
    
def intersection(poly1, poly2, projection, folder):
    ''' Calculates the intersection of two shapefiles and 
        returns intersected 
        Input
        poly1 shapefile
        poly2 shapefile
        projection output projection
        folder ouput folder location
        
        returns the path to output shapefile created'''   
    # calculate the intersection of polygons  
    one = Polygon()
    two = Polygon()
    shp1 = ogr.Open(poly1)
    shp2 = ogr.Open(poly2)
    layer1 = shp1.GetLayer()
    layer2 = shp2.GetLayer()
    for element in layer1:
        geom = loads(element.GetGeometryRef().ExportToWkb())
        one = one.union(geom)
    for element in layer2:
        geom = loads(element.GetGeometryRef().ExportToWkb())
        two = two.union(geom)
    #get geometry of intersection    
    intersect =  ogr.CreateGeometryFromWkb(one.intersection(two).wkb)
    
    # set up tranformation from LatLon to UTM
    in_proj = layer1.GetSpatialRef()
    out_proj = osr.SpatialReference()
    out_proj.ImportFromWkt(projection)  
    transform = osr.CoordinateTransformation(in_proj, out_proj)
    
    driver = ogr.GetDriverByName('Esri Shapefile')
    # creat output layer with single attribute 'id', and 'area'
    outputShapefile = os.path.join(folder, "intersection.shp")
    if os.path.exists(outputShapefile):
        driver.DeleteDataSource(outputShapefile)
    outDS = driver.CreateDataSource(outputShapefile)    
    outLayer = outDS.CreateLayer('intersection', None, ogr.wkbPolygon)
    # ID field creation
    idField = ogr.FieldDefn('id', ogr.OFTInteger)
    outLayer.CreateField(idField)
    # get output layer feature def
    outLayerDefn = outLayer.GetLayerDefn()
    # reproject geometry
    intersect.Transform(transform)
    # create new feature, set geometry and attribute
    outFeature = ogr.Feature(outLayerDefn)
    outFeature.SetGeometry(intersect)
    outFeature.SetField('id', 1)
    outLayer.CreateFeature(outFeature)
    #create prj file for shapefile
    file = open(outputShapefile[:-4] + '.prj', 'w')
    file.write(out_proj.ExportToWkt())
    file.close()
    
    return outputShapefile
        
def createBuffer(inputfn, outputBufferfn, bufferDist):
    if not os.path.isfile(inputfn):
        raise IOError('Could not find file ' + str(inputfn))
    inputds = ogr.Open(inputfn)
    if inputds is None:
        raise IOError('Could not open file ' + str(inputfn))
    inputlyr = inputds.GetLayer()
    spatialRef = inputlyr.GetSpatialRef()
    driver = ogr.GetDriver(0)   #create shapefile
    if os.path.exists(outputBufferfn):
        driver.DeleteDataSource(outputBufferfn)
    out_BuffDS = driver.CreateDataSource(outputBufferfn)
    bufferlyr = out_BuffDS.CreateLayer(outputBufferfn, geom_type=ogr.wkbPolygon)
    # id field creation
    idField = ogr.FieldDefn('id', ogr.OFTInteger)
    bufferlyr.CreateField(idField)
    # area field creation
    areaField = ogr.FieldDefn('area_KM2', ogr.OFTReal)
    areaField.SetWidth(32)
    areaField.SetPrecision(2)
    bufferlyr.CreateField(areaField)
    featureDefn = bufferlyr.GetLayerDefn()

    for i, feature in enumerate(inputlyr):
        buff_geom = feature.geometry().Buffer(bufferDist)
        area = buff_geom.GetArea()
        outFeature = ogr.Feature(featureDefn)
        outFeature.SetGeometry(buff_geom)
        outFeature.SetField('id', 1)
        outFeature.SetField('area_KM2', area/1000000.0) #conversion to KM^2
        bufferlyr.CreateFeature(outFeature)    
    #create prj file for shapefile
    file = open(outputBufferfn[:-4] + '.prj', 'w')
    file.write(spatialRef.ExportToWkt())
    file.close()
    return outputBufferfn
    
def pix_to_tiff(input_rast, output_tif, bits=gdal.GDT_Float32): 
    raster = gdal.Open(input_rast)
    projection = raster.GetProjection()
    cols = raster.RasterXSize
    rows = raster.RasterYSize
    print cols
    print rows
    band = raster.GetRasterBand(1)
    dsm = band.ReadAsArray(0,0, cols, rows)
    dsm[dsm==0] = -9999
    
    geoTransform = raster.GetGeoTransform()
    driver = gdal.GetDriverByName('GTiff')
    outDataset = driver.Create(output_tif, cols, rows, 1, bits)
    outDataset.SetGeoTransform(geoTransform)
    outDataset.SetProjection(projection)
    outDataset.GetRasterBand(1).WriteArray(dsm)
    outDataset.GetRasterBand(1).SetNoDataValue(-9999)
    outDataset.GetRasterBand(1).ComputeStatistics(False)    
    band = None
    raster = None
    
def extent_in_lat_lon(image_path):
    raster = gdal.Open(image_path)
    projection = raster.GetProjection()
    srs = osr.SpatialReference(wkt = projection) 
    geoTransform = raster.GetGeoTransform()
    minx = geoTransform[0]
    maxy = geoTransform[3]
    maxx = minx + geoTransform[1] * raster.RasterXSize
    miny = maxy + geoTransform[5] * raster.RasterYSize
    # Spatial Reference System
    if srs.GetAuthorityCode('projcs'):
        inputEPSG = int(srs.GetAuthorityCode('projcs'))
    else:
        inputEPSG = int(srs.GetAuthorityCode('GEOGCS'))
    outputEPSG = 4326
    
    # create a geometry from coordinates
    point1 = ogr.Geometry(ogr.wkbPoint)
    point1.AddPoint(minx, maxy)
    point2 = ogr.Geometry(ogr.wkbPoint)
    point2.AddPoint(maxx, miny)
    # create coordinate transformation
    inSpatialRef = osr.SpatialReference()
    inSpatialRef.ImportFromEPSG(inputEPSG)
    
    outSpatialRef = osr.SpatialReference()
    outSpatialRef.ImportFromEPSG(outputEPSG)
    
    coordTransform = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)
    
    # transform point
    point1.Transform(coordTransform)
    point2.Transform(coordTransform)
    
    bbox = (point1.GetX(), point2.GetX(), point1.GetY(), point2.GetY())
    return bbox  

def utm_resolution(image_path):
    with ds.open_dataset(image_path) as dataset:
        reader = ds.BasicReader(dataset)
        # determine # of rows and cols       
        cols = reader.width
        rows = reader.height
        # convert lat/lon extent to UTM cooridinates
        extent =  extent_in_lat_lon(image_path) 
        utm_UR = utm.from_latlon(extent[2],extent[0])
        utm_LL = utm.from_latlon(extent[3],extent[1])
        #get distance in x and y directions
        col_dist_m = abs(utm_UR[0] - utm_LL[0])
        row_dist_m = abs(utm_UR[1] - utm_LL[1])
        # calculate resolution in x and y direction
        res_cols = col_dist_m/cols
        res_rows = row_dist_m/rows
        # calculate average resolution
        avg_res = (res_cols + res_rows)/2
    return avg_res
