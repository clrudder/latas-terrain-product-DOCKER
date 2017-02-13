#!/bin/bash

IMAGE=crudder/gbdx-derive-dsm-codetest
NAME=dev_gbdx-derive-dsm-test

docker stop $NAME
docker kill $NAME
docker rm $NAME

docker run \
  --volume /E_DRIVE/DSM/Corpus/working/input/:/mnt/work/input/ \
  --volume /E_DRIVE/DSM/Corpus/working/output/:/mnt/work/output/ \
  --volume /E_DRIVE/DSM/Corpus/working/temp/:/mnt/work/temp/ \
  --name $NAME \
  $IMAGE

docker exec $NAME bash
