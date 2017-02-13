#!/bin/bash

IMAGE=precisionhawk/gbdx-derive-dsm-test
NAME=dev_gbdx-derive-dsm-test

docker stop $NAME
docker kill $NAME
docker rm $NAME

docker run \
  --volume E:/DSM/Corpus/working/input1 \
  --volume E:/DSM/Corpus/working/output \
  --volume E:/DSM/Corpus/working/temp \
  --name $NAME \
  $IMAGE

#docker exec $NAME bash
