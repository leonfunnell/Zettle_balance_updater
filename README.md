  Zettle Balance Updater

Zettle Balance Updater
======================

This project contains a Lambda function that updates the minimum balance on Zettle, since this is not available via the public API. The function is triggered by an API call and accepts the balance, email address, and password as parameters. It uses Selenium and Chromedriver which creates a "headless" Google Chrome browser session. If there are errors in the flow, a log and screenshots will be generated. All sessions will generate logs and screenshots, but a bucket aging policy will mean they will disappear after 7 days.

Setup
-----

1.  Clone the repository:
    
        git clone https://github.com/<your-username>/Zettle_balance_updater.git
        cd Zettle_balance_updater
    
2.  Ensure you are using the correct version of Docker:
    
        docker --version
    
    If your Docker version is outdated, update Docker to the latest version. Here are the steps for updating Docker on different operating systems:
    
    ### For Ubuntu:
    
        
        # Uninstall old versions
        sudo apt-get remove docker docker-engine docker.io containerd runc
        
        # Set up the repository
        sudo apt-get update
        sudo apt-get install \
            apt-transport-https \
            ca-certificates \
            curl \
            gnupg \
            lsb-release
        
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        
        echo \
          "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
          $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # Install Docker Engine
        sudo apt-get update
        sudo apt-get install docker-ce docker-ce-cli containerd.io
        
        # Verify installation
        docker --version
                    
    
3.  Install Docker Buildx:
    
        docker buildx install
    
4.  Build the Docker image and create the deployment package:
    
        ./zip_lambda.sh
    
5.  Deploy the infrastructure using Terraform:
    
        terraform init
        terraform apply
    

API
---

### Request

**POST** `/update_balance`

#### Body

    {
      "email": "your-email@example.com",
      "password": "your-password",
      "min_balance": 300
    }

### Response

#### Success

    {
      "existing_balance": "200",
      "new_balance": "300"
    }

#### Error

    {
      "error": "An error occurred: ...",
      "log_url": "https://your-s3-bucket-name.s3.amazonaws.com/logs/...",
      "screenshot_url": "https://your-s3-bucket-name.s3.amazonaws.com/errors/..."
    }

Notes
-----

*   The Lambda function requires the appropriate binaries and libraries to run `chromedriver` and `selenium`. These dependencies are included in the Docker image used to build the deployment package.
*   Logging is enabled by default, but logs and screenshots are only sent to S3 if an error occurs.