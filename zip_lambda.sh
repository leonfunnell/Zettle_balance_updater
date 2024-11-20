#!/bin/bash

# Ensure Docker Buildx is installed
docker buildx version > /dev/null 2>&1 || {
  echo "Docker Buildx is not installed. Installing..."
  docker buildx install
}

# Create a new builder instance
docker buildx create --use --name izettleminbal-builder

# Build the Docker image using Buildx
docker buildx build --platform linux/amd64 -t izettleminbal-lambda .

# Create a container from the image
container_id=$(docker create izettleminbal-lambda)

# Copy the deployment package from the container
docker cp $container_id:/var/task/izettleminbal.py izettleminbal.py
docker cp $container_id:/var/task/chromedriver chromedriver
docker cp $container_id:/var/task/google-chrome-stable_current_x86_64.rpm google-chrome-stable_current_x86_64.rpm

# Create the deployment package
zip -r izettleminbal.zip izettleminbal.py chromedriver google-chrome-stable_current_x86_64.rpm

# Clean up
docker rm $container_id
rm chromedriver google-chrome-stable_current_x86_64.rpm

# Remove the builder instance
docker buildx rm izettleminbal-builder