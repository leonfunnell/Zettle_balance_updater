#!/bin/bash

# Build the Docker image
docker build -t izettleminbal-lambda .

# Create a container from the image
container_id=$(docker create izettleminbal-lambda)

# Copy the deployment package from the container
docker cp $container_id:/var/task/izettleminbal.py izettleminbal.py
docker cp $container_id:/usr/bin/chromedriver chromedriver
docker cp $container_id:/opt/google/chrome/google-chrome google-chrome

# Create the deployment package
zip -r izettleminbal.zip izettleminbal.py chromedriver google-chrome

# Clean up
docker rm $container_id
rm chromedriver google-chrome