#!/bin/bash
# restarts and removes the volumes from a docker container
docker-compose down -v
docker-compose up -d