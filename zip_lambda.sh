#!/bin/bash

# Build the Docker image
docker build -t izettleminbal-lambda .

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