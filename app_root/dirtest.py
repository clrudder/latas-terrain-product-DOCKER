#!/usr/bin/env python
# encoding=utf8

#############################################################################################
#
#  dirtest.py
#
#  Created by: Matthew Winchester
#              PrecisionHawk
#
#  Version 0.2: October 6, 2016
#               -Can test if a directory is empty and can also delete a directory
#
#  Usage: python dirtest.py
#               Made to be imported and instanced by another class
#
#############################################################################################

#Some test directory you set with file(s) in it. 
#NOTE: This will delete the directory PERMANENTLY on script run. 
TDIR = 'testdir'

import os
import shutil

#Checks if a directory has files in it
def dir_check(dir_path):

    #Bad input
    if not os.path.isdir(dir_path):
        return False

    if len(os.listdir(dir_path)) > 0:
        return True

    return False

#If a directory has files in it, kill them Jimmy. 
def dir_wipe(dir_path):

    if dir_check(dir_path):
        shutil.rmtree(dir_path)
        return True
    else:
        return False

#Add command line parsing if you would like. 
if __name__ == "__main__":

    ret = dir_check(TDIR)
    print ret
    res = dir_wipe(TDIR)
    print res

