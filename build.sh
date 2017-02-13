#!/bin/bash

IMAGE=precisionhawk/gbdx-derive-dsm-test
VERSION=0.01

# Copy over latest version of Geomatica DSM automation script
# TODO Figure out a less fragile way to do this
cp ../../precisionhawk-geomatica/LATAS/*.py app_root/

docker build -t ${IMAGE}:${VERSION} .

docker tag ${IMAGE}:${VERSION} ${IMAGE}:latest

