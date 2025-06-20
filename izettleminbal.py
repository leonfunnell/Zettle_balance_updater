import os
import json
import random
import boto3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from datetime import datetime
import hashlib

# Setup logging
log_filename = datetime.now().strftime("/tmp/izminbaltest_%Y%m%d_%H%M%S.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),  # Log to file
        logging.StreamHandler()  # Log to console
    ]
)

# AWS S3 client
s3_client = boto3.client('s3')
S3_BUCKET = os.getenv("S3_BUCKET")

def upload_to_s3(file_path, bucket, object_name):
    try:
        s3_client.upload_file(file_path, bucket, object_name)
        return f"https://{bucket}.s3.amazonaws.com/{object_name}"
    except Exception as e:
        logging.error(f"Failed to upload {file_path} to S3: {e}")
        return None

def update_min_balance(email, password, min_balance):
    # Setup Chrome options for headless mode
    chrome_options = Options()
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Set up the Chrome driver
    service = Service("/usr/bin/chromedriver")  # Ensure the correct path to chromedriver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Step 1: Log in to the website
        logging.info("Navigating to login page.")
        driver.get("https://login.zettle.com")
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email")))
        
        # Enter email
        logging.info("Entering email.")
        email_field = driver.find_element(By.ID, "email")
        email_field.send_keys(email)
        
        # Click the "Next" button
        logging.info("Clicking 'Next' button.")
        next_button = driver.find_element(By.ID, "submitBtn")
        next_button.click()
        
        # Wait for the password field to be present
        logging.info("Waiting for the password field to be present.")
        screenshot_filename = datetime.now().strftime("/tmp/before_password_field_%Y%m%d_%H%M%S.png")
        driver.save_screenshot(screenshot_filename)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "password")))
        
        # wait for a random time between 4 and 7 seconds
        wait_time = random.randint(4, 7)
        logging.info(f"Waiting for {wait_time} seconds before entering password.")
        time.sleep(wait_time)

        # Enter password
        logging.info("Entering password.")
        password_field = driver.find_element(By.ID, "password")
        password_field.send_keys(password)
        
        # Click the "Log in" button
        logging.info("Clicking 'Log in' button.")
        login_button = driver.find_element(By.ID, "submitBtn")
        login_button.click()
        
        screenshot_filename = datetime.now().strftime("/tmp/after_first_password_field_%Y%m%d_%H%M%S.png")
        driver.save_screenshot(screenshot_filename)
        # Handle "We've detected suspicious behavior" popup if it appears, by looking for text in the popup, not presence of an element
        try:
           if WebDriverWait(driver, 10).until(EC.text_to_be_present_in_element((By.ID, "message"), "We\'ve detected suspicious behavior")):
            logging.info("Suspicious behavior detected. Waiting for 5 seconds before proceeding.") 
            time.sleep(5)  # Wait for 5 seconds to allow the popup to be acknowledged
            # resend the password
            logging.info("Entering password.")
            password_field = driver.find_element(By.ID, "password")
            password_field.send_keys(password)
        except Exception as e:
            logging.info("No suspicious behavior popup found, proceeding with login.")  

        # Handle "Check your email for a code" popup if it appears.  If it does, we need to make an API call to get the code
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'styles__Message-sc-1x8k2qj-0') and contains(text(), 'Check your email for a code')]")))
            logging.info("Check your email for a code popup found. Waiting for 5 seconds before proceeding.")
            time.sleep(5)  # Wait for 5 seconds to allow the popup to be acknowledged
            # Here you would typically make an API call to your email service to get the code
            MakeZettleAPIKey = os.getenv("MAKE_ZETTLE_API_KEY")
            MakeZettleAPIURL = "https://hook.eu1.make.com/7eny3inp4pmpw2xtoxznxtc29tfmkbk8"
            payload = {"x-make-apikey": MakeZettleAPIKey}
            headers = {
                "Content-Type": "application/json"
            }
            response = requests.post(MakeZettleAPIURL, json=payload, headers=headers)
            if response.status_code == 200:
                logging.info("Successfully retrieved code from email.")
                code = response.json().get("code")
                if code:
                    logging.info(f"Code received: {code}")
                    # Enter the code in the input field
                    code_field = driver.find_element(By.ID, "code")
                    code_field.send_keys(code)
                    # Click the "Verify" button
                    verify_button = driver.find_element(By.ID, "submitBtn")
                    verify_button.click()
                else:
                    logging.error("No code found in the response.")
        except Exception as e:
            logging.info("No email code prompt detected, proceeding with login.")

        # Wait for the login to complete
        WebDriverWait(driver, 100).until(EC.url_contains("my.zettle.com"))
        
        # Step 2: Navigate to the account settings page
        logging.info("Navigating to account settings page.")
        driver.get("https://my.zettle.com/settings/account")
        
        # Handle "Accept all cookies" popup if it appears
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "onetrust-accept-btn-handler")))
            accept_cookies_button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
            accept_cookies_button.click()
            logging.info("Clicked 'Accept all cookies' button.")
        except Exception as e:
            logging.info("No 'Accept all cookies' button found.")
        
        # Wait for the settings page to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "styles__InputMemoized-zettle__sc-lm4axe-0")))
        
        # Update the minimum balance
        logging.info("Updating minimum balance.")
        min_balance_field = driver.find_element(By.CSS_SELECTOR, "input[aria-label^='£']")
        existing_value = min_balance_field.get_attribute("value")
        logging.info(f"Existing minimum balance value: {existing_value}")
        
        if existing_value == str(min_balance):
            logging.info("Minimum balance is already set to the desired value. No update needed.")
            return existing_value, existing_value
        
        min_balance_field.clear()
        min_balance_field.send_keys(Keys.CONTROL + "a")
        min_balance_field.send_keys(Keys.DELETE)
        min_balance_field.send_keys(str(min_balance))
        
        # Submit the form or save changes (assuming there's a save button)
        logging.info("Saving changes.")
        save_button = driver.find_element(By.XPATH, "//button[@aria-label='Save']")
        save_button.click()
        
        # Confirm success (you can modify this according to the success message or behavior)
        time.sleep(3)
        logging.info("Minimum balance updated successfully.")
        
        # Re-read the minimum balance to ensure it has been updated
        driver.refresh()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label^='£']")))
        new_min_balance_field = driver.find_element(By.CSS_SELECTOR, "input[aria-label^='£']")
        new_min_balance_value = new_min_balance_field.get_attribute("value")
        logging.info(f"New minimum balance value: {new_min_balance_value}")
        
        return existing_value, new_min_balance_value
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        error_screenshot_filename = datetime.now().strftime("/tmp/error_screenshot_%Y%m%d_%H%M%S.png")
        driver.save_screenshot(error_screenshot_filename)
        error_screenshot_url = upload_to_s3(error_screenshot_filename, S3_BUCKET, f"errors/{os.path.basename(error_screenshot_filename)}")
        log_url = upload_to_s3(log_filename, S3_BUCKET, f"logs/{os.path.basename(log_filename)}")
        raise Exception(f"An error occurred: {e}", {"log_url": log_url, "screenshot_url": error_screenshot_url})
    finally:
        driver.quit()

def lambda_handler(event, context):
    try:
        logging.info("Received event: " + json.dumps(event))
        body = json.loads(event['body'])
        email = body['email']
        password = body['password']
        min_balance = body['min_balance']
        
        existing_balance, new_balance = update_min_balance(email, password, min_balance)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'existing_balance': existing_balance,
                'new_balance': new_balance
            })
        }
    except Exception as e:
        logging.error(f"An error occurred in lambda_handler: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': str(e),
                'log_url': e.args[1].get('log_url'),
                'screenshot_url': e.args[1].get('screenshot_url')
            })
        }

# main
if __name__ == "__main__":
    email = os.getenv("IZETTLE_EMAIL")
    password = os.getenv("IZETTLE_PASSWORD")
    min_balance = os.getenv("MIN_BALANCE")
    # Create JSON and call lambda_handler so we can test the function locally
    event = {
        "body": json.dumps({
            "email": email,
            "password": password,
            "min_balance": min_balance
        })
    }
    lambda_handler(event, None)

# End of izettleminbal.py
