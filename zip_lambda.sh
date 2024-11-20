#!/bin/bash

# Build the Docker image
docker build -t izettleminbal-lambda .

# Create a container from the image
container_id=$(docker create izettleminbal-lambda)

# Copy the necessary files from the container
docker cp $container_id:/var/task/izettleminbal.py izettleminbal.py
docker cp $container_id:/usr/bin/chromedriver chromedriver
docker cp $container_id:/opt/google/chrome/google-chrome google-chrome
docker cp $container_id:/var/task/selenium selenium
docker cp $container_id:/var/task/boto3 boto3
docker cp $container_id:/var/task/botocore botocore
docker cp $container_id:/var/task/s3transfer s3transfer
docker cp $container_id:/var/task/urllib3 urllib3
docker cp $container_id:/var/task/requests requests
docker cp $container_id:/var/task/certifi certifi
docker cp $container_id:/var/task/chardet chardet
docker cp $container_id:/var/task/idna idna
docker cp $container_id:/var/task/websocket websocket
docker cp $container_id:/var/task/chromedriver chromedriver

# Create the deployment package
zip -r izettleminbal.zip izettleminbal.py chromedriver google-chrome selenium boto3 botocore s3transfer urllib3 requests certifi chardet idna websocket

# Clean up
docker rm $container_id
rm -rf chromedriver google-chrome selenium boto3 botocore s3transfer urllib3 requests certifi chardet idna websocket