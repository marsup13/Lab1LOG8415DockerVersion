#!/bin/bash

#####################################################BUILD AND RUN THE DOCKER CONTAINER#######################################################


#SEE ALSO https://github.com/marsup13/lab1LOG8415
#SEE FULL CODE IN https://github.com/marsup13/Lab1LOG8415DockerVersion

docker build -t docker-metrics:latest .
docker run --name metricsapp -v$PWD/app:/app -p5000:5000 docker-metrics:latest







