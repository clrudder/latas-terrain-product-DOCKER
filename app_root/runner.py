#!/usr/bin/env python
# encoding=utf8

#############################################################################################
#
#  runner.py
#
#  Created by: Matthew Winchester
#              PrecisionHawk
#
#  Version 0.2: August 30, 2016
#               -Wrapper to DSM_from_Stereo.py, used in a docker container on gbdx
#  Usage: python runner.py
#               
#############################################################################################

import genDSM as gendsm

import json
import os
import shutil
import sys

OUTFILE         = "/mnt/work/output/data_log"
INFILE          = "/mnt/work/input/"
TMPDIR          = "/mnt/work/tmp"


#super hard coded for testing
STATUS_PATH     = "/mnt/work/status.json"
TILE_SHP_TEST   = "TILE_SHAPE.shp"

INPUT_PORTS = '/mnt/work/input/ports.json'
OUTPUT_PORTS = '/mnt/work/output/ports.json'

#Returns the task inputs inside ports.json
def parse_ports():
    with open(INPUT_PORTS) as portsfile:
        return json.load(portsfile)

#JSON functions to writeout the task result status
def success(reason):
    with open(STATUS_PATH, "w") as outfile:
        json.dump({"status":"success" ,"reason":reason}, outfile, indent=4)

def failure(reason):
    with open(STATUS_PATH, "w") as outfile:
        json.dump({"status":"failed" , "reason":reason}, outfile, indent=4)


if __name__ == "__main__":
        print "starting DSM task"
        try:
                code = gendsm.process(INFILE, OUTFILE, TMPDIR)
                success(code)
        except Exception as e:
                print e.__doc__
                print e.message
                failure("bad code here")


