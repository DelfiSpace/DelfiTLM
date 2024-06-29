#!/bin/bash
# run Docker Compose, rebuild the images and run in server mode
docker compose -f docker-compose.yml -f docker-compose-deploy.yml up --build -d
