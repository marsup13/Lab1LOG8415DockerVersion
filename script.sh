#/bin/bash

docker build -t tp1-docker --secret id=aws,src=$HOME/.aws/credentials .
docker run tp1-docker
