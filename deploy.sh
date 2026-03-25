#!/bin/bash

set -e

cd ~/app

git pull

docker stop autonews-worker 2>/dev/null || true
docker rm autonews-worker 2>/dev/null || true

docker stop autonews-upload-api 2>/dev/null || true
docker rm autonews-upload-api 2>/dev/null || true

docker build -t autonews .

docker run -d \
  --name autonews-worker \
  --restart always \
  --env-file ~/app/.env \
  -e PYTHONUNBUFFERED=1 \
  -v ~/app/output:/app/output \
  autonews

docker run -d \
  --name autonews-upload-api \
  --restart always \
  --env-file ~/app/.env \
  -e PYTHONUNBUFFERED=1 \
  -v ~/app/output:/app/output \
  -p 8080:8080 \
  autonews \
  python api_server.py

docker ps --filter name=autonews-worker --filter name=autonews-upload-api
echo
echo "Scheduler logs: docker logs -f autonews-worker"
echo "Upload API logs: docker logs -f autonews-upload-api"