#!/usr/bin/env python
# encoding=utf8

#############################################################################################
#
#  wcs_req.py
#
#  Created by: Matthew Winchester
#              PrecisionHawk
#
#  Version 0.1: Oct 17, 2016
#               - Used to issue WCS requests to a specific endpoint.
#
#  Usage:python wcs_req.py
#
#############################################################################################

import os
from PIL import Image
import bs4 as bs
import pycurl
from cStringIO import StringIO

import requests
import json

#Our lovely hardcoded endpoint on the terrain server
#ENDPOINT = 'https://terrain-dev.flylatas.com/OGC/'
ENDPOINT = 'https://esri-test.precisionhawk.com/arcgisserver/rest/services/SRTM_v3/SRTM_V3_USGS/ImageServer/exportImage?'

#Endpoint service definitions
WCS = 'SERVICE=WCS'

#Issues request to PH-terrain ESRI image export service. 
def export_image(points, path, crs="4326", gridoff="1000,1000"):

    url = get_json(points, crs, gridoff)
    return get_image_from_endpoint(url, path)

#Uses the ESRI endpoint to collect and parse json to find the sub image location.
def get_json(points, crs="4326", gridoff="1000,1000"):

    headers = {"Accept" : 'application/json'}

    filetype = 'f=json'
    formats = '&FORMAT=tiff'
    values  = ','.join(str(x) for x in points)
    bbox = '&bbox=' + values
    crsstr  = '&imagesSR=' + crs + '&bboxSR=' + crs

    gridstr = '&size=' + str(gridoff)

    type = "&pixelType=S16"
    url = ENDPOINT + filetype + formats + bbox + type + crsstr + gridstr

    print "URL: ", url

    response = requests.get(url, headers=headers)

    img_data = json.loads(response.content)

    return img_data['href']

#Collects an image from a URL and saves it to path. Designed to work with ESRI JSON standards. 
def get_image_from_endpoint(url, path):

    target = os.path.join(path, 'dem.tif')

    f = open(target, 'wb')
    f.write(requests.get(url).content)
    f.close()

    return target

#Grab the geotiff coverage of a given AOI bounding box and image
def get_coverage(identifier, points, path="", crs="4326", gridoff="0.0002777777777,0.0002777777777", file='json'):

    buffer = StringIO()
    c = pycurl.Curl()

    #Prepare input values
    request = '&REQUEST=GetCoverage'
    filetype = 'f=' + file
    #version = '&VERSION=' + version
    version = ''
    iden    = '&IDENTIFIER=' + identifier
    iden = ''

    formats = '&FORMAT=tiff'
    #formats = ''
    #parse co-ordinates in array to string values
    values  = ','.join(str(x) for x in points)
    bbox    = '&bbox=' + values
    crsstr  = '&imagesSR=' + crs + '&bboxSR=' + crs
    gridstr = '&size=' + str(gridoff)
    req = ENDPOINT + filetype + formats + bbox + crsstr + gridstr
    print "URL: ", req

    c.setopt(c.URL, req)

    target = os.path.join(path, 'dem.tif')
    print target
    with open(target, 'wb') as f:
        c.setopt(c.WRITEFUNCTION, f.write)
        c.perform()
        c.close()

    return target


#Grab the capabilities based on version number (ex: 1.1.0)
def get_capabilities_req(version='1.1.0'):

    #Parse response as plain-text

    buffer = StringIO()
    c = pycurl.Curl()
    url = ENDPOINT + WCS + '&REQUEST=GetCapabilities&VERSION='+ version
    
    c.setopt(c.URL, url)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    c.close()

    return buffer.getvalue()


#Grab the list of operational capabilities
def list_capabilities(content):

    return list_key(content, 'Operation', False)


#Grab identifiers (names) of the published data for WCS
def list_identifiers(content):

    return list_key(content, 'Identifier', True)


#Parse the xml stack for a given key
def list_key(content, key, toString=True):

    body = []

    soup = bs.BeautifulSoup(content, 'xml')

    iden = soup.Identifier

    for k in soup.find_all(key):
        if toString:
            body.append(k.string)
        else:
            body.append(str(k))

    return body


#Simple Driver
if __name__ == "__main__":


    #body = get_capabilities_req('1.1.0')
    #print body
    #print list_identifiers(body)
    #print list_capabilities(body)
    #coords = [-78.819049,35.715808,-78.471063,35.971728]
    coords = [-79.212328021,35.94547359,-78.2774247423,36.09214008]
    #get_coverage("PH-ELEV", coords)
    #get_coverage("SRTM_V3_USGS", coords, path='/Users/mwinchester/test/dems', gridoff="0.0002777777777,0.0002777777777")
    export_image(coords, path='/Users/mwinchester/test/dems', gridoff="1000,1000")






