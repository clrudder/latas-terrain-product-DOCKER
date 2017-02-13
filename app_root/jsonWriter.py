#!/usr/bin/env python
# encoding=utf8

#############################################################################################
#
#  jsonWriter.py
#
#  Created by: Matthew Winchester
#              PrecisionHawk
#
#  Version 0.1: September 27, 2016
#               -writes json from proc_dsm.py for success and errors
#  Usage: <imported and ran>
#               
#############################################################################################



import json
import os

#Simple class that writes erros to a given static directory. Uses GBDX protocol. 
class jsonWriter(object):

    def __init__(self, base_dir):
        self.status_path = base_dir

    def getPath(self):
        return self.status_path

    #JSON functions to writeout the task result status
    def failure(self, reason):
        path = self.getPath()
        with open(os.path.join(path, "status.json"), "w") as outfile:
            json.dump({"status":"failed" , "reason":reason}, outfile, indent=4)


#Simple driver
if __name__ == "__main__":

    print "Trivial Test"
    jw = jsonWriter("/home/mwinchester/test/")
    jw.failure("dope")



