#!/bin/sh

# Set LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# Don't let the process exit
while true; do sleep 1000; done
