#!/bin/bash
# resets and removes the volumes from a docker container
docker-compose down
docker rm -f $(docker ps -a -q)
docker volume rm $(docker volume ls -q)
docker-compose up -d