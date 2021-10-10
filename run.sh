#!/bin/bash

#####################################################BUILD AND RUN THE DOCKER CONTAINER#######################################################


docker build -t docker-metrics:latest .
docker run --name metricsapp -v$PWD/app:/app -p5000:5000 docker-metrics:latest







