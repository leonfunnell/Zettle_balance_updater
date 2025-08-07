import os
import json
import random
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import logging  # Import the logging module
from datetime import datetime

# === CONFIGURATION ===
EMAIL = "email@address.com"
PASSWORD = "<password>"
CODE_API_ENDPOINT = "https://apiendpoint.com/endpoint"  # Change this to your actual endpoint
API_KEY = "<APIKEY>"
CHROME_DRIVER_PATH = "/usr/bin/chromedriver"  # Update this
min_balance = 850  # Set your desired minimum balance here
LOG_FILE_PATH = "/tmp/izminbaltest.log"  # Log file path

chrome_options = Options()
chrome_options.add_argument("--headless=new")  # Comment this out to see the browser
chrome_options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=chrome_options)

# Set up logging
log_filename = datetime.now().strftime("/tmp/izminbaltest_%Y%m%d_%H%M%S.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename),  # Log to file
        logging.StreamHandler()  # Log to console
    ]
)

def wait_for_element(by, value, timeout=10):
    for _ in range(timeout):
        try:
            return driver.find_element(by, value)
        except NoSuchElementException:
            time.sleep(1)
    raise TimeoutException(f"Timeout waiting for element: {value}")

def check_suspicious_behaviour():
    try:
        header_elem = driver.find_element(By.XPATH, "//p[contains(text(), 'suspicious behaviour')]")
        if "suspicious behaviour" in header_elem.text.lower():
            logging.warning("[!] Suspicious behaviour detected.")
            return True
    except NoSuchElementException:
        pass
    return False

def login():
    logging.info("[*] Navigating to login.zettle.com")
    driver.get("https://login.zettle.com/")
    
    logging.info("[*] Entering email")
    wait_for_element(By.ID, "email").send_keys(EMAIL)
    wait_for_element(By.ID, "submitBtn").click()

    logging.info("[*] Entering password")
    time.sleep(3)
    password_field = wait_for_element(By.ID, "password")
    for char in PASSWORD:
        password_field.send_keys(char)
        time.sleep(random.uniform(0.2, 0.7))  # Random delay between 0.2 and 0.7 seconds
    wait_for_element(By.ID, "submitBtn").click()
    time.sleep(3)

    if check_suspicious_behaviour():
        logging.info("[*] Re-entering password after suspicious behaviour warning")
        password_field = wait_for_element(By.ID, "password")
        password_field.clear()
        for char in PASSWORD:
            password_field.send_keys(char)
            time.sleep(random.uniform(0.2, 0.7))  # Random delay between 0.2 and 0.7 seconds
        wait_for_element(By.ID, "submitBtn").click()
    time.sleep(3)

    # Handle 2FA email code
    if "check your email for a code" in driver.page_source.lower():
        try:
            logging.info("[*] 2FA required - retrieving code from API...")
            headers = {"x-make-apikey": API_KEY}
            response = requests.get(CODE_API_ENDPOINT, headers=headers)
            response.raise_for_status()
            code = response.json().get("code")
            if not code:
                raise Exception("No code found in API response")
            logging.info(f"[*] Entering verification code: {code}")
            # Locate the OTP input fields and type each digit
            otp_inputs = driver.find_elements(By.CSS_SELECTOR, ".otp-box.otp-input")
            for i, digit in enumerate(code):
                otp_inputs[i].send_keys(digit)
            wait_for_element(By.ID, "submitBtn").click()
        except Exception as e:
            logging.error(f"[!] Failed to retrieve or enter 2FA code: {e}")
            raise

    # Handle "Accept all cookies" popup if it appears
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "onetrust-accept-btn-handler")))
        accept_cookies_button = driver.find_element(By.ID, "onetrust-accept-btn-handler")
        accept_cookies_button.click()
        logging.info("Clicked 'Accept all cookies' button.")
    except Exception as e:
        logging.info("No 'Accept all cookies' button found.")
    return

def update_minimum_balance(min_balance):
    logging.info("[*] Navigating to account settings page...")
    driver.get("https://my.zettle.com/settings/account")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "styles__InputMemoized-zettle__sc-lm4axe-0")))
    logging.info("[*] Navigated to account settings page.")

    min_balance_field = driver.find_element(By.CSS_SELECTOR, "input[aria-label^='£']")
    existing_value = min_balance_field.get_attribute("value")
    logging.info(f"[*] Current minimum balance: {existing_value}")
    if existing_value == str(min_balance):
        logging.info("Minimum balance is already set to the desired value. No update needed.")
        return existing_value

    min_balance_field.clear()
    min_balance_field.send_keys(Keys.CONTROL + "a")
    min_balance_field.send_keys(Keys.DELETE)
    min_balance_field.send_keys(str(min_balance))
    logging.info(f"[*] Updated minimum balance to: {min_balance}")
    save_button = driver.find_element(By.XPATH, "//button[@aria-label='Save']")
    save_button.click()
    return existing_value

try:
    login()
    logging.info("[+] Login successful.")
    time.sleep(2)
    current_balance = update_minimum_balance(min_balance)
    logging.info(f"[+] Minimum balance updated from: {current_balance} to: {min_balance}")
    logging.info("[*] Script completed successfully.")
except TimeoutException as te:
    logging.error(f"[!] Timeout occurred: {te}")
except NoSuchElementException as ne:
    logging.error(f"[!] Element not found: {ne}")
except requests.RequestException as re:
    logging.error(f"[!] API request failed: {re}")
except KeyboardInterrupt:
    logging.warning("[!] Script interrupted by user.")
except ValueError as ve:
    logging.error(f"[!] Value error: {ve}")
except Exception as ex:
    logging.error(f"[!] Login failed: {ex}")
finally:
    time.sleep(5)
    driver.quit()
