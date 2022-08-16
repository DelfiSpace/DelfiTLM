#!/bin/bash
docker-compose -f docker-compose.yml -f docker-compose-deploy.yml up --build
# docker-compose -f docker-compose.yml -f docker-compose-deploy.yml up
