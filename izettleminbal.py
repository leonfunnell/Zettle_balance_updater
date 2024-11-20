import os
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

# Configuration
EMAIL = "leon_funnell@hotmail.com"  # Replace with your email
PASSWORD = os.getenv("IZPASSWORD")  # Fetch password from environment variable
MIN_BALANCE = 300                # Replace with the desired minimum balance

if not PASSWORD:
    raise EnvironmentError("IZPASSWORD environment variable is not set.")

# Setup logging
log_filename = datetime.now().strftime("izettleminbal_%Y%m%d_%H%M%S.log")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=log_filename)

def update_min_balance():
    # Setup Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Set up the Chrome driver
    service = Service("/usr/bin/chromedriver")  # Replace with the correct path to chromedriver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Step 1: Log in to the website
        logging.info("Navigating to login page.")
        driver.get("https://login.zettle.com")
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email")))
        
        # Enter email
        logging.info("Entering email.")
        email_field = driver.find_element(By.ID, "email")
        email_field.send_keys(EMAIL)
        
        # Click the "Next" button
        logging.info("Clicking 'Next' button.")
        next_button = driver.find_element(By.ID, "submitBtn")
        next_button.click()
        
        # Wait for the password field to be present
        logging.info("Waiting for the password field to be present.")
        screenshot_filename = datetime.now().strftime("before_password_field_%Y%m%d_%H%M%S.png")
        driver.save_screenshot(screenshot_filename)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "password")))
        
        # Enter password
        logging.info("Entering password.")
        password_field = driver.find_element(By.ID, "password")
        password_field.send_keys(PASSWORD)
        
        # Click the "Log in" button
        logging.info("Clicking 'Log in' button.")
        login_button = driver.find_element(By.ID, "submitBtn")
        login_button.click()
        
        # Wait for the login to complete
        WebDriverWait(driver, 10).until(EC.url_contains("my.zettle.com"))
        
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
        
        if existing_value == str(MIN_BALANCE):
            logging.info("Minimum balance is already set to the desired value. No update needed.")
            return
        
        min_balance_field.clear()
        min_balance_field.send_keys(Keys.CONTROL + "a")
        min_balance_field.send_keys(Keys.DELETE)
        min_balance_field.send_keys(str(MIN_BALANCE))
        
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
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        error_screenshot_filename = datetime.now().strftime("error_screenshot_%Y%m%d_%H%M%S.png")
        driver.save_screenshot(error_screenshot_filename)
    finally:
        driver.quit()

if __name__ == "__main__":
    update_min_balance()
