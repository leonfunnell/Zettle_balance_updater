import os
import json
import random
import time
import requests
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import logging
from datetime import datetime

# === CONFIGURATION ===
CHROME_DRIVER_PATH = "/usr/bin/chromedriver"  # Update this
LOG_FILE_PATH = "/tmp/izminbaltest.log"  # Log file path
KNOWN_API_KEY = "your_known_api_key"  # Replace with your actual API key

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

# FastAPI setup
app = FastAPI()

# API Key validation
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=True)

def validate_api_key(api_key: str = Depends(api_key_header)):
    if api_key != KNOWN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

# Request model
class UpdateMinBalanceRequest(BaseModel):
    email: str
    password: str
    min_balance: int
    code_api_endpoint: str
    code_api_key: str

# Selenium setup
chrome_options = Options()
chrome_options.add_argument("--headless=new")  # Comment this out to see the browser
chrome_options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=chrome_options)

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

def login(email, password, code_api_endpoint, code_api_key):
    logging.info("[*] Navigating to login.zettle.com")
    driver.get("https://login.zettle.com/")
    
    logging.info("[*] Entering email")
    wait_for_element(By.ID, "email").send_keys(email)
    wait_for_element(By.ID, "submitBtn").click()

    logging.info("[*] Entering password")
    time.sleep(3)
    password_field = wait_for_element(By.ID, "password")
    for char in password:
        password_field.send_keys(char)
        time.sleep(random.uniform(0.2, 0.7))  # Random delay between 0.2 and 0.7 seconds
    wait_for_element(By.ID, "submitBtn").click()
    time.sleep(3)

    if check_suspicious_behaviour():
        logging.info("[*] Re-entering password after suspicious behaviour warning")
        password_field = wait_for_element(By.ID, "password")
        password_field.clear()
        for char in password:
            password_field.send_keys(char)
            time.sleep(random.uniform(0.2, 0.7))  # Random delay between 0.2 and 0.7 seconds
        wait_for_element(By.ID, "submitBtn").click()
    time.sleep(3)

    # Handle 2FA email code
    if "check your email for a code" in driver.page_source.lower():
        try:
            logging.info("[*] 2FA required - retrieving code from API...")
            headers = {"x-make-apikey": code_api_key}
            response = requests.get(code_api_endpoint, headers=headers)
            response.raise_for_status()
            code = response.json().get("code")
            if not code:
                raise Exception("No code found in API response")
            logging.info(f"[*] Entering verification code: {code}")
            otp_inputs = driver.find_elements(By.CSS_SELECTOR, ".otp-box.otp-input")
            for i, digit in enumerate(code):
                otp_inputs[i].send_keys(digit)
            wait_for_element(By.ID, "submitBtn").click()
        except Exception as e:
            logging.error(f"[!] Failed to retrieve or enter 2FA code: {e}")
            raise

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

@app.post("/update-min-balance", dependencies=[Depends(validate_api_key)])
def update_min_balance_endpoint(request: UpdateMinBalanceRequest):
    try:
        login(request.email, request.password, request.code_api_endpoint, request.code_api_key)
        logging.info("[+] Login successful.")
        time.sleep(2)
        current_balance = update_minimum_balance(request.min_balance)
        logging.info(f"[+] Minimum balance updated from: {current_balance} to: {request.min_balance}")
        return {"status": "success", "current_balance": current_balance, "updated_balance": request.min_balance}
    except Exception as ex:
        logging.error(f"[!] Failed to update minimum balance: {ex}")
        raise HTTPException(status_code=500, detail=str(ex))
    finally:
        time.sleep(5)
        driver.quit()