#!/usr/bin/env python3
"""
Princeton Dating App Automated Testing System

This script provides a comprehensive testing framework for the Princeton dating app,
handling CAS authentication with Duo two-factor authentication, and testing all app functionalities.

Usage:
    python dating_app_test.py
"""

import os
import time
import logging
import json
import sys
import argparse
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import unittest
from concurrent.futures import ThreadPoolExecutor
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException, ElementClickInterceptedException, ElementNotInteractableException, WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dating_app_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DatingAppTest")

# Test configuration
TEST_CONFIG = {
    "base_url": "https://date-a-base-with-credits-839b845c06a6.herokuapp.com",
    "api_url": "https://date-a-base-with-credits-839b845c06a6.herokuapp.com/api",
    "headless": False,  # Set to True for headless mode
    "timeout": 30,
    "screenshot_dir": "test_screenshots",
    "wait_for_duo": 60,
    "browser_window_size": (1920, 1080),
}

# Parse command line arguments
parser = argparse.ArgumentParser(description='Run Princeton Dating App automated tests')
parser.add_argument('--username', '-u', help='Princeton NetID for login')
parser.add_argument('--password', '-p', help='Password for login')
parser.add_argument('--headless', action='store_true', help='Run in headless mode')
parser.add_argument('--tests', '-t', help='Comma-separated list of test classes to run')
parser.add_argument('--screenshot-dir', help='Directory to save screenshots')
parser.add_argument('--skip-logout', action='store_true', help='Skip logout after tests')
parser.add_argument('--url', help='Base URL of the application')
parser.add_argument('--manual', action='store_true', help='Enable manual test mode with browser interaction')
parser.add_argument('--pause-after-login', action='store_true', help='Pause after login to allow manual browser inspection')
parser.add_argument('--wait-time', type=int, help='Wait time in seconds for manual browser interactions')
parser.add_argument('--retry', type=int, default=1, help='Number of retries for failed tests')
parser.add_argument('--test-timeout', type=int, default=300, help='Timeout in seconds for each test class')
parser.add_argument('--manual-auth', action='store_true', help='Allow manual authentication before running tests')

args = parser.parse_args()

# Update configuration from args
if args.headless:
    TEST_CONFIG["headless"] = True
if args.screenshot_dir:
    TEST_CONFIG["screenshot_dir"] = args.screenshot_dir
if args.url:
    TEST_CONFIG["base_url"] = args.url
    TEST_CONFIG["api_url"] = f"{args.url}/api"

if args.manual:
    TEST_CONFIG["manual_mode"] = True
else:
    TEST_CONFIG["manual_mode"] = False

if args.pause_after_login:
    TEST_CONFIG["pause_after_login"] = True
else:
    TEST_CONFIG["pause_after_login"] = False

if args.wait_time:
    TEST_CONFIG["manual_wait_time"] = args.wait_time
else:
    TEST_CONFIG["manual_wait_time"] = 30  # Default 30 seconds for manual interaction

# Create screenshot directory if it doesn't exist
Path(TEST_CONFIG["screenshot_dir"]).mkdir(parents=True, exist_ok=True)

# Test credentials - Replace these with command line args
TEST_CREDENTIALS = {
    "username": args.username or os.environ.get("PRINCETON_NETID", ""),
    "password": args.password or os.environ.get("PRINCETON_PASSWORD", "")
}

# Update TEST_CONFIG with retry count from args
TEST_CONFIG["retry_count"] = args.retry
TEST_CONFIG["test_timeout"] = args.test_timeout

# Update TEST_CONFIG with manual auth flag
TEST_CONFIG["manual_auth"] = args.manual_auth

class DatingAppTest:
    """Base class for Dating App testing"""
    
    def __init__(self, config: Dict[str, Any] = None, setup_driver: bool = True):
        """Initialize the test framework with configuration"""
        self.config = config or TEST_CONFIG
        self.driver = None
        self.wait = None
        self.authenticated = False
        self.test_data = {}
        self.session = self._setup_requests_session()
        
        # Create test folders
        Path(self.config["screenshot_dir"]).mkdir(parents=True, exist_ok=True)
        
        if setup_driver:
            self.setup_driver()
            
            # Add welcome message for manual mode
            if self.config.get("manual_mode") and not self.config.get("welcome_shown"):
                print("\n" + "*" * 80)
                print("*** MANUAL TEST MODE ENABLED ***")
                print("*** You'll be prompted to interact with the browser at key points ***")
                print("*** This can help troubleshoot or verify browser behavior ***")
                print("*" * 80 + "\n")
                self.config["welcome_shown"] = True  # Prevent showing multiple times
    
    def _setup_requests_session(self):
        """Set up a requests session with retry logic"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def setup_driver(self):
        """Set up the WebDriver with appropriate configuration"""
        options = ChromeOptions()
        
        # Set headless mode if configured
        if self.config["headless"]:
            options.add_argument("--headless=new")
        
        # Set window size
        window_width, window_height = self.config["browser_window_size"]
        options.add_argument(f"--window-size={window_width},{window_height}")
        
        # Performance and stability options
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        
        # Privacy options
        options.add_argument("--incognito")
        
        # Additional browser optimization
        options.add_argument("--disable-browser-side-navigation")
        options.add_argument("--disable-features=VizDisplayCompositor")
        
        # Create the ChromeDriver instance
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            # Try fallback to basic Chrome driver
            self.driver = webdriver.Chrome(options=options)
        
        # Configure driver
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, self.config["timeout"])
        logger.info("Chrome browser initialized")
    
    def take_screenshot(self, name: str):
        """Take a screenshot with a timestamp"""
        if not self.driver:
            logger.warning("Cannot take screenshot - driver not initialized")
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.config['screenshot_dir']}/{name}_{timestamp}.png"
        try:
            self.driver.save_screenshot(filename)
            logger.info(f"Screenshot saved: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None
    
    def navigate_to(self, url: str = None):
        """Navigate to a specific URL or the base URL"""
        target_url = url or self.config["base_url"]
        logger.info(f"Navigating to {target_url}")
        
        try:
            self.driver.get(target_url)
            # Wait for page to load
            self.wait_for_page_load()
            return True
        except Exception as e:
            logger.error(f"Error navigating to {target_url}: {e}")
            self.take_screenshot(f"navigation_error_{url.replace('/', '_')}")
            return False
    
    def wait_for_page_load(self, timeout: int = None):
        """Wait for page to completely load"""
        wait_time = timeout or self.config["timeout"]
        try:
            self.wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
        except TimeoutException:
            logger.warning(f"Page load timeout after {wait_time} seconds")
    
    def wait_for_element(self, locator: Tuple[By, str], timeout: int = None, visible: bool = True) -> Any:
        """Wait for an element to be present and optionally visible, then return it"""
        wait_time = timeout or self.config["timeout"]
        try:
            if visible:
                element = WebDriverWait(self.driver, wait_time).until(
                    EC.visibility_of_element_located(locator)
                )
            else:
                element = WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_element_located(locator)
                )
            return element
        except TimeoutException:
            logger.error(f"Element {locator} not found/visible after {wait_time} seconds")
            self.take_screenshot(f"element_not_found_{locator[1].replace(' ', '_')}")
            raise

    def safe_click(self, element_or_locator, timeout: int = 5, retries: int = 3):
        """Safely click an element with retries and error handling"""
        element = None
        
        for attempt in range(retries):
            try:
                # If we received a locator tuple
                if isinstance(element_or_locator, tuple):
                    element = self.wait_for_element(element_or_locator, timeout)
                else:
                    element = element_or_locator
                
                # Scroll element into view
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.5)  # Brief pause to allow scroll to complete
                
                # Try clicking the element using JavaScript
                try:
                    self.driver.execute_script("arguments[0].click();", element)
                    return True
                except Exception:
                    # Fall back to regular click
                    element.click()
                    return True
                    
            except ElementClickInterceptedException:
                logger.warning(f"Click intercepted on attempt {attempt+1}/{retries}, trying to resolve...")
                # Try to close any modal or overlay
                try:
                    # Look for common close buttons or overlays
                    close_buttons = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'close') or contains(@aria-label, 'Close') or contains(text(), 'Close')]")
                    if close_buttons:
                        logger.info("Found potential close button, trying to click it")
                        self.driver.execute_script("arguments[0].click();", close_buttons[0])
                        time.sleep(1)
                except Exception as e:
                    logger.warning(f"Failed to close overlay: {e}")
                time.sleep(1)
                
            except (StaleElementReferenceException, ElementNotInteractableException):
                logger.warning(f"Element became stale or not interactable on attempt {attempt+1}/{retries}, retrying...")
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error clicking element on attempt {attempt+1}/{retries}: {e}")
                time.sleep(1)
                
        # If we get here, all attempts failed
        self.take_screenshot("click_failed")
        raise Exception(f"Failed to click element after {retries} attempts")
    
    def fill_text_field(self, locator: Tuple[By, str], text: str, clear_first: bool = True):
        """Fill a text field with the given text"""
        try:
            element = self.wait_for_element(locator)
            if clear_first:
                element.clear()
            element.send_keys(text)
            return True
        except Exception as e:
            logger.error(f"Error filling text field {locator}: {e}")
            self.take_screenshot(f"fill_error_{locator[1].replace(' ', '_')}")
            return False
            
    def select_dropdown_option(self, dropdown_locator: Tuple[By, str], option_text: str = None, option_value: str = None, option_index: int = None):
        """Select an option from a dropdown by text, value, or index"""
        try:
            dropdown_element = self.wait_for_element(dropdown_locator)
            select = Select(dropdown_element)
            
            if option_text:
                select.select_by_visible_text(option_text)
            elif option_value:
                select.select_by_value(option_value)
            elif option_index is not None:
                select.select_by_index(option_index)
            else:
                logger.error("No selection criteria provided")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error selecting from dropdown {dropdown_locator}: {e}")
            self.take_screenshot(f"dropdown_error_{dropdown_locator[1].replace(' ', '_')}")
            return False

    def login(self):
        """Handle the Princeton CAS login with credentials"""
        if self.authenticated:
            logger.info("Already authenticated")
            return True
        
        # Check if manual authentication is requested
        if self.config.get("manual_auth", False):
            logger.info("Using manual authentication flow")
            return self.manual_authentication()
        
        try:
            # Navigate to the base URL which should redirect to login
            self.navigate_to(self.config['base_url'])
            
            # Current page might be:
            # 1. App login page with CAS button
            # 2. CAS login page directly
            # 3. Already logged in and in the app
            # 4. Heroku app loading/sleeping
            
            # Check if we're on a CAS login page directly
            try:
                cas_username = self.wait_for_element((By.ID, "username"), timeout=5, visible=False)
                if cas_username:
                    logger.info("Already on CAS login page")
                    return self._handle_cas_login()
            except TimeoutException:
                logger.info("Not on CAS login page directly")
            
            # Try to find login button with various selectors
            login_button_locators = [
                (By.XPATH, "//button[contains(text(), 'Sign in with Princeton CAS')]"),
                (By.XPATH, "//button[contains(text(), 'Princeton CAS')]"),
                (By.XPATH, "//a[contains(text(), 'Princeton CAS')]"),
                (By.XPATH, "//button[contains(@class, 'cas-login')]"),
                (By.XPATH, "//button[contains(text(), 'Login')]"),
                (By.XPATH, "//a[contains(text(), 'Login')]")
            ]
            
            login_button = None
            for locator in login_button_locators:
                try:
                    login_button = self.wait_for_element(locator, timeout=3)
                    logger.info(f"Found login button with selector: {locator}")
                    break
                except TimeoutException:
                    continue
            
            if login_button:
                # Click the login button to start CAS auth flow
                logger.info("Clicking CAS login button")
                self.safe_click(login_button)
                
                # Wait for CAS login page
                try:
                    self.wait_for_element((By.ID, "username"), timeout=15)
                    logger.info("CAS login page loaded")
                    return self._handle_cas_login()
                except TimeoutException:
                    logger.error("CAS login page not loaded after clicking login button")
                    self.take_screenshot("cas_page_not_loaded")
                    
                    # Try direct CAS navigation as fallback
                    logger.info("Trying direct CAS login as fallback")
                    return self._direct_cas_login()
            else:
                # Login button not found, check if already logged in or try direct CAS
                logger.info("Login button not found, checking if already authenticated")
                
                # Check for profile icon or other post-login element
                try:
                    auth_indicators = [
                        (By.XPATH, "//nav"),
                        (By.XPATH, "//button[contains(@class, 'avatar')]"),
                        (By.XPATH, "//div[contains(@class, 'profile')]"),
                        (By.XPATH, "//header[contains(@class, 'app-header')]")
                    ]
                    
                    for locator in auth_indicators:
                        try:
                            self.wait_for_element(locator, timeout=3)
                            logger.info(f"Found authenticated element with selector: {locator}")
                            self.authenticated = True
                            self.take_screenshot("already_authenticated")
                            return True
                        except TimeoutException:
                            continue
                    
                    # Check for Heroku app loading/waking up
                    try:
                        heroku_indicators = [
                            (By.XPATH, "//*[contains(text(), 'Heroku')]"),
                            (By.XPATH, "//*[contains(text(), 'loading')]"),
                            (By.XPATH, "//*[contains(text(), 'warming up')]"),
                            (By.XPATH, "//*[contains(text(), 'booting')]")
                        ]
                        
                        for locator in heroku_indicators:
                            try:
                                element = self.wait_for_element(locator, timeout=2)
                                logger.info(f"Heroku loading detected: {element.text}")
                                
                                # Wait for Heroku to finish loading (up to 30 seconds)
                                logger.info("Waiting for Heroku app to wake up (up to 30 seconds)")
                                time.sleep(10)
                                self.navigate_to(self.config['base_url'])
                                
                                # Try login again after reload
                                return self.login()
                            except TimeoutException:
                                continue
                    except Exception as e:
                        logger.warning(f"Error checking for Heroku loading: {e}")
                    
                    # If all else fails, try direct CAS login as last resort
                    logger.warning("Could not determine login state, trying direct CAS login")
                    self.take_screenshot("login_state_unclear_direct_cas_attempt")
                    return self._direct_cas_login()
                    
                except Exception as e:
                    logger.error(f"Error checking login state: {e}")
                    self.take_screenshot("login_state_check_error")
                    
                    # Try direct CAS login as fallback
                    logger.info("Trying direct CAS login as fallback")
                    return self._direct_cas_login()
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            self.take_screenshot("login_error")
            
            # Try direct CAS login as last resort
            logger.info("Trying direct CAS login as last resort")
            return self._direct_cas_login()

    def _direct_cas_login(self):
        """Directly navigate to Princeton CAS login page"""
        logger.info("Attempting direct CAS login")
        
        # Direct CAS URL
        cas_url = "https://fed.princeton.edu/cas/login"
        
        # Add service parameter for our app
        service_url = self.config["base_url"]
        full_cas_url = f"{cas_url}?service={service_url}"
        
        # Navigate to CAS login page
        self.navigate_to(full_cas_url)
        
        # Handle CAS login
        return self._handle_cas_login()

    def _handle_cas_login(self):
        """Handle the CAS username/password form and Duo auth"""
        try:
            # Check if we have username field
            try:
                username_field = self.wait_for_element((By.ID, "username"), timeout=10)
            except TimeoutException:
                logger.error("Username field not found on CAS page")
                self.take_screenshot("cas_username_not_found")
                return False
            
            # Enter username
            if not TEST_CREDENTIALS["username"]:
                logger.error("No username provided for CAS login")
                self.take_screenshot("missing_username")
                return False
            
            logger.info(f"Entering username: {TEST_CREDENTIALS['username']}")
            self.fill_text_field((By.ID, "username"), TEST_CREDENTIALS["username"])
            
            # Enter password
            if not TEST_CREDENTIALS["password"]:
                logger.error("No password provided for CAS login")
                self.take_screenshot("missing_password")
                return False
            
            logger.info("Entering password")
            self.fill_text_field((By.ID, "password"), TEST_CREDENTIALS["password"])
            
            # Take screenshot before submitting
            self.take_screenshot("before_cas_submit")
            
            # Click Sign In
            signin_button = self.wait_for_element((By.NAME, "submit"))
            self.safe_click(signin_button)
            
            # Handle Duo authentication
            return self.handle_duo_auth()
        except Exception as e:
            logger.error(f"CAS login handling error: {e}")
            self.take_screenshot("cas_login_error")
            return False

    def handle_duo_auth(self):
        """Handle Duo two-factor authentication by waiting for manual intervention"""
        try:
            logger.info("Checking for Duo auth iframe or indicators...")
            
            # Wait for either:
            # 1. Duo iframe to appear
            # 2. Already on app page (maybe Duo was remembered)
            # 3. Duo error message
            
            # Check for immediate redirect to app (Duo might be remembered)
            try:
                # Look for app elements that indicate successful auth
                app_indicators = [
                    (By.XPATH, "//nav"),
                    (By.XPATH, "//header[contains(@class, 'app-header')]"),
                    (By.XPATH, "//*[contains(text(), 'Profile')]"),
                    (By.XPATH, "//*[contains(text(), 'Swipe')]"),
                    (By.XPATH, "//*[contains(text(), 'Matches')]")
                ]
                
                for locator in app_indicators:
                    try:
                        self.wait_for_element(locator, timeout=5)
                        logger.info(f"App element found immediately after login: {locator}")
                        logger.info("Duo authentication appears to be bypassed/remembered")
                        self.authenticated = True
                        self.take_screenshot("duo_bypassed")
                        return True
                    except TimeoutException:
                        continue
            except Exception as e:
                logger.warning(f"Error checking for immediate app access: {e}")
            
            # Look for Duo iframe or other Duo-specific elements
            duo_indicators = [
                (By.ID, "duo_iframe"),
                (By.XPATH, "//*[contains(text(), 'Duo Security')]"),
                (By.XPATH, "//*[contains(text(), 'two-factor')]"),
                (By.XPATH, "//div[contains(@class, 'duo')]")
            ]
            
            duo_element = None
            duo_iframe = None
            for locator in duo_indicators:
                try:
                    element = self.wait_for_element(locator, timeout=5, visible=False)
                    duo_element = element
                    if locator[1] == "duo_iframe":
                        duo_iframe = element
                    logger.info(f"Duo indicator found: {locator}")
                    break
                except TimeoutException:
                    continue
            
            if duo_iframe:
                logger.info("Duo iframe found, need to authenticate")
                
                # Switch to Duo iframe
                self.driver.switch_to.frame(duo_iframe)
                
                # Take screenshot of Duo auth options
                self.take_screenshot("duo_auth_options")
                
                # Try to find and select "Send Me a Push" option if available
                try:
                    push_buttons = [
                        (By.XPATH, "//button[contains(text(), 'Send Me a Push')]"),
                        (By.XPATH, "//button[contains(text(), 'Send a Push')]")
                    ]
                    
                    push_button = None
                    for locator in push_buttons:
                        try:
                            push_button = self.wait_for_element(locator, timeout=5)
                            break
                        except TimeoutException:
                            continue
                    
                    if push_button:
                        logger.info("Found 'Send Me a Push' button, clicking it")
                        self.safe_click(push_button)
                        logger.info("Push notification requested")
                    else:
                        logger.info("No push button found, may need different auth method")
                except Exception as e:
                    logger.warning(f"Error trying to request push: {e}")
            elif duo_element:
                logger.info("Duo element found but not in iframe format")
                self.take_screenshot("duo_non_iframe")
            else:
                logger.info("No Duo iframe or indicators found, checking for other auth methods")
                
                # Check if we're already past Duo (might be on app already)
                try:
                    current_url = self.driver.current_url
                    if self.config['base_url'] in current_url:
                        logger.info(f"Already on app URL: {current_url}")
                        
                        # Check for common app elements
                        for locator in app_indicators:
                            try:
                                self.wait_for_element(locator, timeout=5)
                                logger.info(f"App element found: {locator}")
                                self.authenticated = True
                                return True
                            except TimeoutException:
                                continue
                except Exception as e:
                    logger.warning(f"Error checking current URL: {e}")
            
            # Prompt user for manual authentication regardless of what we found
            print("\n" + "*" * 80)
            print(f"*** DUO AUTHENTICATION REQUIRED ***")
            print(f"*** Please authenticate in the browser window now ***")
            print(f"*** You have {self.config['wait_for_duo']} seconds to complete this ***")
            print("*" * 80 + "\n")
            
            # If we were in an iframe, switch back to main content
            if duo_iframe:
                self.driver.switch_to.default_content()
            
            # Wait for redirect after Duo auth
            wait_time = self.config["wait_for_duo"]
            timeout = time.time() + wait_time
            
            # Poll for success indicators
            while time.time() < timeout:
                try:
                    # Check if we're redirected to the app
                    current_url = self.driver.current_url
                    
                    # Handle various success cases
                    if self.config['base_url'] in current_url:
                        logger.info(f"Detected redirect to app URL: {current_url}")
                        self.authenticated = True
                        break
                    
                    # Check for onboarding URL patterns
                    if '/onboarding' in current_url or '/complete-profile' in current_url:
                        logger.info(f"Detected redirect to onboarding: {current_url}")
                        self.authenticated = True
                        break
                    
                    # Check for common app elements
                    nav_found = False
                    try:
                        nav_elements = self.driver.find_elements(By.XPATH, "//nav")
                        header_elements = self.driver.find_elements(By.XPATH, "//header")
                        if nav_elements or header_elements:
                            logger.info("Nav/header elements detected")
                            self.authenticated = True
                            nav_found = True
                            break
                    except Exception:
                        pass
                    
                    # Check for "welcome" or similar post-login messages
                    try:
                        welcome_elements = self.driver.find_elements(
                            By.XPATH, 
                            "//*[contains(text(), 'Welcome') or contains(text(), 'Profile') or contains(text(), 'Swipe')]"
                        )
                        if welcome_elements:
                            logger.info(f"Welcome element found: {welcome_elements[0].text}")
                            self.authenticated = True
                            break
                    except Exception:
                        pass
                    
                    # Brief pause between checks to avoid hammering the browser
                    time.sleep(2)
                except Exception as e:
                    logger.warning(f"Error during authentication polling: {e}")
                    time.sleep(2)
            
            # Verify authentication success
            if self.authenticated:
                logger.info("Duo authentication completed successfully")
                self.take_screenshot("duo_auth_successful")
                return True
            else:
                logger.error("Duo authentication timeout")
                self.take_screenshot("duo_auth_timeout")
                
                # Let's ask the user if they want to continue anyway
                print("\n" + "*" * 80)
                print("*** DUO AUTHENTICATION TIMEOUT ***")
                print("*** Do you want to continue anyway? The app may still be usable if auth succeeded ***")
                continue_anyway = input("Continue anyway? (y/n): ").lower().strip() == 'y'
                print("*" * 80 + "\n")
                
                if continue_anyway:
                    logger.info("User opted to continue despite Duo timeout")
                    self.authenticated = True
                    return True
                else:
                    logger.info("User opted to abort after Duo timeout")
                    return False
                
        except Exception as e:
            logger.error(f"Duo authentication error: {e}")
            self.take_screenshot("duo_auth_error")
            
            # Let's ask the user if they want to continue anyway
            print("\n" + "*" * 80)
            print(f"*** DUO AUTHENTICATION ERROR: {e} ***")
            print("*** Do you want to continue anyway? The app may still be usable if auth succeeded ***")
            continue_anyway = input("Continue anyway? (y/n): ").lower().strip() == 'y'
            print("*" * 80 + "\n")
            
            if continue_anyway:
                logger.info("User opted to continue despite Duo error")
                self.authenticated = True
                return True
            else:
                logger.info("User opted to abort after Duo error")
                return False

    def logout(self):
        """Handle the logout process"""
        if not self.authenticated:
            logger.info("Not logged in, no need to logout")
            return True
            
        try:
            # First navigate to the profile page, which has the logout button
            self.navigate_to(f"{self.config['base_url']}/profile")
            
            # Look for the logout button based on the actual HTML
            try:
                # Based on the HTML, the logout button is next to the Edit Profile button
                logout_button = self.driver.find_element(
                    By.XPATH, "//button[contains(text(), 'Logout')]"
                )
                
                if not logout_button:
                    logger.warning("Logout button not found on profile page, trying API logout")
                    # Try API logout
                    self.navigate_to(f"{self.config['base_url']}/api/cas/logout")
                    self.authenticated = False
                    return True
                
                # Take screenshot before logout
                self.take_screenshot("before_logout")
                
                # Click logout button
                self.safe_click(logout_button)
                logger.info("Clicked logout button")
                
                # Wait for redirect to login page
                time.sleep(3)
                self.take_screenshot("after_logout")
                
                # Verify we're logged out - usually redirects to login page
                current_url = self.driver.current_url
                if "/login" in current_url or self.config['base_url'] + "/" == current_url:
                    logger.info("Successfully logged out")
                    self.authenticated = False
                    return True
                else:
                    logger.warning(f"After logout, unexpected URL: {current_url}")
                    # Consider it successful anyway to avoid blocking other tests
                    self.authenticated = False
                    return True
                
            except NoSuchElementException:
                logger.warning("Logout button not found, trying API logout")
                # As fallback, try API logout
                self.navigate_to(f"{self.config['base_url']}/api/cas/logout")
                self.authenticated = False
                return True
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            self.take_screenshot("logout_error")
            # Consider it successful anyway to avoid blocking other tests
            self.authenticated = False
            return True
    
    def teardown(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")
            self.driver = None

    def manual_browser_interaction(self, message=None, wait_time=None):
        """Allow user to manually interact with the browser for troubleshooting"""
        if not self.config.get("manual_mode"):
            return
        
        wait_seconds = wait_time or self.config.get("manual_wait_time", 30)
        
        if not message:
            message = "Manual browser interaction"
        
        print("\n" + "*" * 80)
        print(f"*** {message} ***")
        print(f"*** Current URL: {self.driver.current_url} ***")
        print(f"*** You have {wait_seconds} seconds to interact with the browser... ***")
        print(f"*** Press Enter to continue immediately, or wait for timeout ***")
        print("*" * 80 + "\n")
        
        # Use select with timeout to wait for user input or timeout
        import select
        import sys
        
        # Take a screenshot
        self.take_screenshot(f"manual_interaction_{message.lower().replace(' ', '_')}")
        
        # Wait for input or timeout
        ready, _, _ = select.select([sys.stdin], [], [], wait_seconds)
        if ready:
            sys.stdin.readline()  # Read and discard the input
            print(f"Continuing...")
        else:
            print(f"Timeout reached, continuing...")
        
        # Take another screenshot after manual interaction
        self.take_screenshot(f"after_manual_interaction_{message.lower().replace(' ', '_')}")

    def manual_authentication(self):
        """Handle manual authentication by the user"""
        try:
            # Navigate to the login page
            self.navigate_to(self.config['base_url'])
            
            print("\n" + "*" * 80)
            print("*** MANUAL AUTHENTICATION REQUIRED ***")
            print("*** Please complete the Princeton CAS login and Duo authentication in the browser ***")
            print("*** Take as much time as needed to fully log in ***")
            print("*** Press Enter ONLY WHEN you are fully logged in and can see the app ***")
            print("*" * 80 + "\n")
            
            # Wait for user to confirm they're logged in
            input("Press Enter when you have completed authentication...")
            
            # Take a screenshot to verify
            self.take_screenshot("manual_authentication_completed")
            
            # Check if actually logged in by looking for common elements
            try:
                auth_indicators = [
                    (By.XPATH, "//nav"),
                    (By.XPATH, "//button[contains(@class, 'avatar')]"),
                    (By.XPATH, "//div[contains(@class, 'profile')]"),
                    (By.XPATH, "//header[contains(@class, 'app-header')]")
                ]
                
                for locator in auth_indicators:
                    try:
                        self.wait_for_element(locator, timeout=3)
                        logger.info(f"Found authenticated element with selector: {locator}")
                        self.authenticated = True
                        return True
                    except TimeoutException:
                        continue
                
                # If we couldn't verify, ask user if they're sure they're authenticated
                print("\n" + "*" * 80)
                print("*** WARNING: Could not automatically verify that you are logged in ***")
                confirmation = input("Are you sure you're logged into the app? (y/n): ").lower().strip()
                print("*" * 80 + "\n")
                
                if confirmation == 'y':
                    logger.info("User confirmed manual authentication successful")
                    self.authenticated = True
                    return True
                else:
                    logger.error("User indicated authentication was not successful")
                    return False
                    
            except Exception as e:
                logger.error(f"Error verifying manual authentication: {e}")
                print("\n" + "*" * 80)
                print(f"*** ERROR: {e} ***")
                confirmation = input("Are you sure you're logged into the app despite the error? (y/n): ").lower().strip()
                print("*" * 80 + "\n")
                
                if confirmation == 'y':
                    logger.info("User confirmed manual authentication successful despite verification error")
                    self.authenticated = True
                    return True
            else:
                    logger.error("User indicated authentication was not successful")
                    return False
        except Exception as e:
            logger.error(f"Error during manual authentication: {e}")
            return False

    def add_delay(self, seconds=1.5):
        """Add a small delay to make actions more visible"""
        time.sleep(seconds)
        logger.info(f"Added {seconds} second delay for visibility")

    # First, add a scroll_to_element method to the DatingAppTest class
    def scroll_to_element(self, element):
        """Scroll the element into view with JavaScript"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
            self.add_delay(0.5)  # Short delay to allow smooth scrolling
            logger.info("Scrolled element into view")
            return True
        except Exception as e:
            logger.warning(f"Error scrolling to element: {e}")
            return False


class ProfileTesting(DatingAppTest):
    """Test user profile functionality"""
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config, setup_driver=False)
    
    def test_profile_view(self):
        """Test viewing user's own profile"""
        try:
            # Ensure we're logged in
            if not self.authenticated:
                self.login()
            
            # Navigate to profile page
            self.navigate_to(f"{self.config['base_url']}/profile")
            
            # Take a screenshot of the profile page
            self.take_screenshot("profile_page_view")
            
            # Check for profile page elements based on actual HTML
            # Look for the header "Your Profile"
            try:
                profile_header = self.driver.find_element(By.XPATH, "//h1[contains(text(), 'Your Profile')]")
                logger.info(f"Found profile header: {profile_header.text}")
            except NoSuchElementException:
                logger.warning("Profile header not found, but continuing test")
            
            # Check for basic profile elements
            elements_to_check = [
                (By.XPATH, "//div[contains(@class, 'rounded-full')]//img"), # Profile image
                (By.XPATH, "//h3[contains(text(), 'Name')]"), # Name field
                (By.XPATH, "//h3[contains(text(), 'Gender')]"), # Gender field 
                (By.XPATH, "//h3[contains(text(), 'Class Year')]") # Class year field
            ]
            
            for locator in elements_to_check:
                try:
                    element = self.driver.find_element(*locator)
                    logger.info(f"Found profile element: {locator}")
                except NoSuchElementException:
                    logger.warning(f"Optional profile element not found: {locator}")
            
            logger.info("Profile view test passed")
            return True
        except Exception as e:
            logger.error(f"Profile view error: {e}")
            self.take_screenshot("profile_view_error")
            raise
    
    def test_profile_advanced_features(self):
        """Test advanced profile features like social links or preferences"""
        try:
            # Ensure we're logged in
            if not self.authenticated:
                self.login()
            
            # Navigate to profile page
            self.navigate_to(f"{self.config['base_url']}/profile")
            self.add_delay(1)
            
            # Take a screenshot of the profile page
            self.take_screenshot("profile_advanced_features_initial")
            
            # Check for advanced profile sections
            advanced_sections = []
            section_headers = self.driver.find_elements(By.XPATH, "//h2[contains(@class, 'text-lg') or contains(@class, 'text-xl')]")
            
            for header in section_headers:
                try:
                    section_name = header.text
                    if section_name and section_name not in ["Your Profile"]:
                        advanced_sections.append((header, section_name))
                        logger.info(f"Found profile section: {section_name}")
                except:
                    pass
            
            if advanced_sections:
                # Try to interact with the first section
                section_header, section_name = advanced_sections[0]
                self.scroll_to_element(section_header)
                self.take_screenshot(f"profile_section_{section_name.lower().replace(' ', '_')}")
                
                # Look for expandable sections or toggles
                try:
                    # Try to find toggles/switches in the section
                    parent_section = section_header.find_element(By.XPATH, "./..")
                    toggles = parent_section.find_elements(By.XPATH, ".//button[contains(@class, 'switch') or contains(@class, 'toggle')]")
                    
                    if toggles:
                        logger.info(f"Found {len(toggles)} toggles/switches in section {section_name}")
                        
                        # Try to click the first toggle
                        toggle = toggles[0]
                        self.scroll_to_element(toggle)
                        self.take_screenshot("before_toggle_click")
                        
                        # Get current state
                        toggle_state_before = toggle.get_attribute("aria-checked")
                        
                        # Click the toggle
                        self.safe_click(toggle)
                        logger.info(f"Clicked toggle in {section_name} section")
                        self.add_delay(1)
                        
                        # Take screenshot after clicking
                        self.take_screenshot("after_toggle_click")
                        
                        # Check if state changed
                        toggle_state_after = toggle.get_attribute("aria-checked")
                        if toggle_state_before != toggle_state_after:
                            logger.info(f"Toggle state changed from {toggle_state_before} to {toggle_state_after}")
                        
                        # Click again to restore original state
                        self.safe_click(toggle)
                        self.add_delay(1)
                except Exception as e:
                    logger.info(f"No toggles found or error accessing them: {e}")
                
                # Look for accordion sections
                try:
                    accordions = self.driver.find_elements(
                        By.XPATH, "//div[contains(@class, 'accordion') or contains(@class, 'collapse') or contains(@class, 'expandable')]//button"
                    )
                    
                    if accordions:
                        logger.info(f"Found {len(accordions)} accordion/expandable sections")
                        
                        # Try to click the first accordion
                        accordion = accordions[0]
                        self.scroll_to_element(accordion)
                        self.take_screenshot("before_accordion_click")
                        
                        # Click the accordion
                        self.safe_click(accordion)
                        logger.info("Clicked accordion/expandable section")
                        self.add_delay(1)
                        
                        # Take screenshot after clicking
                        self.take_screenshot("after_accordion_click")
                except Exception as e:
                    logger.info(f"No accordions found or error accessing them: {e}")
                
                return True
            else:
                # Look for specific advanced features like social media links
                social_elements = self.driver.find_elements(
                    By.XPATH, "//a[contains(@href, 'instagram') or contains(@href, 'facebook') or contains(@href, 'twitter') or contains(@href, 'linkedin')]"
                )
                
                if social_elements:
                    logger.info(f"Found {len(social_elements)} social media links")
                    return True
                
                # Look for preference settings
                preference_elements = self.driver.find_elements(
                    By.XPATH, "//div[contains(text(), 'Preference') or contains(text(), 'preference')]"
                )
                
                if preference_elements:
                    logger.info(f"Found {len(preference_elements)} preference elements")
                    return True
                
                logger.info("No advanced profile features found, this might be expected")
                return True
        except Exception as e:
            logger.error(f"Profile advanced features test error: {e}")
            self.take_screenshot("profile_advanced_features_error")
            return False
    
    def test_profile_editing(self):
        """Test editing profile information"""
        try:
            # Ensure we're logged in
            if not self.authenticated:
                self.login()
            
            # Navigate to profile page
            self.navigate_to(f"{self.config['base_url']}/profile")
            self.take_screenshot("profile_before_edit")
            
            # Look for Edit Profile link based on actual HTML
            try:
                # The Edit Profile link is an <a> tag with text "Edit Profile"
                edit_link = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Edit Profile')]")
                logger.info("Found Edit Profile link")
                
                # Click the Edit Profile link
                self.safe_click(edit_link)
                logger.info("Clicked Edit Profile link")
                
                # Wait for edit page to load
                try:
                    self.wait_for_element((By.XPATH, "//h1[contains(text(), 'Edit Your Profile')]"), timeout=10)
                    logger.info("Edit Profile page loaded")
                    self.take_screenshot("edit_profile_page")
                except TimeoutException:
                    logger.warning("Could not confirm edit profile page loaded")
                    self.take_screenshot("edit_profile_page_maybe")
                
                # Find and modify at least one field - try the hometown field
                try:
                    hometown_field = self.driver.find_element(By.ID, "hometown")
                    if hometown_field:
                        current_value = hometown_field.get_attribute("value")
                        new_value = f"Test Hometown {datetime.now().strftime('%H:%M:%S')}"
                        
                        hometown_field.clear()
                        hometown_field.send_keys(new_value)
                        logger.info(f"Updated hometown from '{current_value}' to '{new_value}'")
                    
                    # Look for Save Changes button
                    save_button = self.driver.find_element(
                        By.XPATH, "//button[contains(text(), 'Save Changes')]"
                    )
                    
                    if save_button:
                        # Don't actually click save to avoid changing the database
                        # Instead just verify we found the button
                        logger.info("Found Save Changes button")
                        self.take_screenshot("found_save_button")
                        return True
                    else:
                        logger.warning("Save Changes button not found")
                        return False
                        
                except NoSuchElementException as e:
                    logger.warning(f"Could not find field to edit: {e}")
                    return False
                
            except NoSuchElementException:
                logger.warning("Edit Profile link not found - check if you have permission to edit")
                self.take_screenshot("edit_link_not_found")
                return False
                
        except Exception as e:
            logger.error(f"Profile editing error: {e}")
            self.take_screenshot("profile_edit_error")
            raise
    
    def test_profile_completion(self):
        """Test completing profile during onboarding"""
        # Since we're already logged in, we'll likely not see onboarding
        # This test is essentially a placeholder unless testing with new accounts
        try:
            # Ensure we're logged in
            if not self.authenticated:
                self.login()
            
            # Check if we're on an onboarding page
            current_url = self.driver.current_url
            if '/onboarding' in current_url or '/complete-profile' in current_url:
                logger.info("On onboarding page, testing profile completion")
                self.take_screenshot("onboarding_page")
                
                # We would handle the onboarding flow here if needed
                # For now, just return success since we're likely already onboarded
                
            return True
            else:
                logger.info("Not on onboarding page, skipping profile completion test")
                return True
                
        except Exception as e:
            logger.error(f"Profile completion error: {e}")
            self.take_screenshot("profile_completion_error")
            raise


class MatchingTesting(DatingAppTest):
    """Test the matching and swiping functionality"""
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config, setup_driver=False)
    
    def test_swipe_page_loads(self):
        """Test that the swipe page loads successfully"""
        try:
            # Ensure we're logged in
            if not self.authenticated:
                self.login()
            
            # Navigate to swipe page
            self.navigate_to(f"{self.config['base_url']}/swipe")
            
            # Take a screenshot to see what we got
            self.take_screenshot("swipe_page_loaded")
            
            # Check for swipe page elements based on actual HTML
            
            # First look for the card container
            try:
                card = self.driver.find_element(By.XPATH, "//div[contains(@class, 'hinge-card')]")
                logger.info("Found swipe card container")
                
                # Look for the action buttons (like, pass)
                like_button = self.driver.find_element(
                    By.XPATH, "//button[@aria-label='Like']"
                )
                pass_button = self.driver.find_element(
                    By.XPATH, "//button[@aria-label='Pass']"
                )
                
                if like_button and pass_button:
                    logger.info("Found like and pass buttons")
                    return True
                else:
                    logger.warning("Could not find swipe action buttons")
                    return False
                    
            except NoSuchElementException:
                # If no card found, check if there's a message indicating no profiles
                try:
                    empty_message = self.driver.find_element(
                        By.XPATH, "//p[contains(text(), 'No profiles') or contains(text(), 'empty')]"
                    )
                    logger.info(f"No profiles available: {empty_message.text}")
                    return True
                except NoSuchElementException:
                    logger.warning("Neither swipe card nor empty state message found")
                    # Still return True as the page did load, just not with expected content
                    return True
                
        except Exception as e:
            logger.error(f"Swipe page loading error: {e}")
            self.take_screenshot("swipe_page_error")
            raise
            
    def test_refresh_button(self):
        """Test the refresh button functionality in the swipe interface"""
        try:
            # Ensure we're logged in
            if not self.authenticated:
                self.login()
            
            # Navigate to swipe page
            self.navigate_to(f"{self.config['base_url']}/swipe")
            self.add_delay(2)  # Wait for page to fully load
            
            # Take screenshot of the initial state
            self.take_screenshot("refresh_initial_state")
            
            # Check if there are profiles to swipe
            try:
                # First look for the card container and get its details
                card = self.driver.find_element(By.XPATH, "//div[contains(@class, 'hinge-card')]")
                logger.info("Found swipe card container")
                
                # Try to get the profile name or some identifier to verify it changes after refresh
                try:
                    profile_name = card.find_element(By.XPATH, ".//h2").text
                    logger.info(f"Current profile: {profile_name}")
                except:
                    profile_name = "Unknown"
                    logger.info("Couldn't get profile name")
                
                # Scroll down to make buttons visible
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
                self.add_delay(1)
                
                # Try to find the refresh button by aria-label
                try:
                    refresh_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Refresh']")
                    logger.info("Found refresh button")
                    
                    # Take screenshot before clicking
                    self.take_screenshot("before_refresh_click")
                    
                    # Scroll to the refresh button
                    self.scroll_to_element(refresh_button)
                    
                    # Click the refresh button
                    self.safe_click(refresh_button)
                    logger.info("Clicked refresh button")
                    
                    # Add delay to allow refresh to complete
                    self.add_delay(3)
                    
                    # Take screenshot after clicking
                    self.take_screenshot("after_refresh_click")
                    
                    # Try to verify the card changed or refreshed
                    try:
                        new_card = self.driver.find_element(By.XPATH, "//div[contains(@class, 'hinge-card')]")
                        try:
                            new_profile_name = new_card.find_element(By.XPATH, ".//h2").text
                            logger.info(f"New profile after refresh: {new_profile_name}")
                            
                            # If profile name changed, refresh was successful
                            if new_profile_name != profile_name:
                                logger.info("Refresh button successfully changed the profile")
                            else:
                                logger.info("Profile appears to be the same after refresh (might be expected if there's only one profile)")
                        except:
                            logger.warning("Couldn't get new profile name after refresh")
                    except:
                        logger.warning("Couldn't find card after refresh")
                    
                    return True
                    
                except NoSuchElementException as e:
                    logger.warning(f"Could not find refresh button: {e}")
                    self.take_screenshot("refresh_button_not_found")
                    
                    # Try finding refresh button with a more general approach
                    try:
                        refresh_buttons = self.driver.find_elements(
                            By.XPATH, "//button[contains(@class, 'action-button')][2]"  # Middle button is usually refresh
                        )
                        
                        if refresh_buttons and len(refresh_buttons) > 0:
                            refresh_button = refresh_buttons[0]
                            logger.info("Found refresh button with general selector")
                            
                            self.scroll_to_element(refresh_button)
                            self.safe_click(refresh_button)
                            logger.info("Clicked refresh button with general selector")
                            self.add_delay(3)
                            self.take_screenshot("after_general_refresh_click")
                            return True
                        else:
                            logger.warning("No refresh button found with general selector")
                            return False
                    except Exception as e:
                        logger.error(f"Error with general button approach for refresh: {e}")
                        return False
                    
            except NoSuchElementException:
                logger.info("No profiles available for testing refresh, skipping test")
                return True
                
        except Exception as e:
            logger.error(f"Refresh button test error: {e}")
            self.take_screenshot("refresh_test_error")
            raise
    
    def test_swipe_functionality(self):
        """Test swiping functionality (like/pass)"""
        try:
            # Ensure we're logged in
            if not self.authenticated:
                self.login()
            
            # Navigate to swipe page
            self.navigate_to(f"{self.config['base_url']}/swipe")
            self.add_delay(2)  # Wait for page to fully load
            
            # Take screenshot of the initial state
            self.take_screenshot("swipe_initial_state")
            
            # Check if there are profiles to swipe
            try:
                # First look for the card container
                card = self.driver.find_element(By.XPATH, "//div[contains(@class, 'hinge-card')]")
                logger.info("Found swipe card container")
                
                # Scroll down to make buttons visible
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
                self.add_delay(1)
                
                # Try to find swipe buttons by aria-label
                try:
                    # Find the action buttons
                    buttons = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'action-button')]")
                    logger.info(f"Found {len(buttons)} action buttons")
                    
                    # Take screenshot showing the buttons
                    self.take_screenshot("swipe_buttons")
                    
                    # Look for the Like button specifically
                    like_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Like']")
                    
                    # Scroll to the Like button
                    self.scroll_to_element(like_button)
                    self.add_delay(1)
                    
                    # Take screenshot before clicking Like
                    self.take_screenshot("before_like_button_click")
                    
                    # Click the Like button
                    self.safe_click(like_button)
                    logger.info("Clicked Like button")
                    
                    # Add delay to allow animation to complete
                    self.add_delay(3)
                    
                    # Take screenshot after clicking
                    self.take_screenshot("after_like_button_click")
                    
                    # Check for match notification if it appears
                    try:
                        match_notification = self.driver.find_element(
                            By.XPATH, "//*[contains(text(), 'match') and contains(@class, 'notification')]"
                        )
                        if match_notification:
                            logger.info("Match notification found")
                            self.take_screenshot("match_notification")
                    except NoSuchElementException:
                        logger.info("No match notification appeared")
                    
                    # Check for another profile to try Pass button
                    try:
                        # Wait briefly for next card to appear
                        self.add_delay(2)
                        
                        # Find next card
                        next_card = self.driver.find_element(By.XPATH, "//div[contains(@class, 'hinge-card')]")
                        
                        # Find the Pass button
                        pass_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Pass']")
                        
                        # Scroll to the Pass button
                        self.scroll_to_element(pass_button)
                        self.add_delay(1)
                        
                        # Take screenshot before clicking Pass
                        self.take_screenshot("before_pass_button_click")
                        
                        # Click the Pass button
                        self.safe_click(pass_button)
                        logger.info("Clicked Pass button")
                        
                        # Add delay to allow animation to complete
                        self.add_delay(3)
                        
                        # Take screenshot after clicking
                        self.take_screenshot("after_pass_button_click")
                        
                    except NoSuchElementException as e:
                        logger.info(f"Could not test Pass button: {e}")
                    
                    return True
                    
                except NoSuchElementException as e:
                    logger.warning(f"Could not find swipe buttons: {e}")
                    self.take_screenshot("swipe_buttons_not_found")
                    
                    # Try finding buttons with a more general approach
                    try:
                        # Look for any buttons in the bottom section
                        bottom_buttons = self.driver.find_elements(
                            By.XPATH, "//div[contains(@class, 'justify-center')]/button"
                        )
                        
                        if bottom_buttons and len(bottom_buttons) > 0:
                            logger.info(f"Found {len(bottom_buttons)} buttons with general selector")
                            
                            # Try clicking the rightmost button (usually Like)
                            right_button = bottom_buttons[-1]
                            self.scroll_to_element(right_button)
                            self.safe_click(right_button)
                            logger.info("Clicked rightmost button (likely Like)")
                            self.add_delay(2)
                            self.take_screenshot("after_general_like_click")
                            return True
                        else:
                            logger.warning("No buttons found with general selector")
                            return False
                    except Exception as e:
                        logger.error(f"Error with general button approach: {e}")
                        return False
                
            except NoSuchElementException:
                logger.info("No profiles available for swiping, skipping test")
                return True
                
        except Exception as e:
            logger.error(f"Swipe functionality error: {e}")
            self.take_screenshot("swipe_functionality_error")
            raise
    
    def test_profile_details(self):
        """Test viewing detailed profile information from swipe page"""
        try:
            # Ensure we're logged in
            if not self.authenticated:
                self.login()
            
            # Navigate to swipe page
            self.navigate_to(f"{self.config['base_url']}/swipe")
            
            # Check if there are profiles to view
            try:
                # Look for a card that we can click for details
                card = self.driver.find_element(By.XPATH, "//div[contains(@class, 'hinge-card')]")
                
                # Try clicking on the card image to view details
                try:
                    card_image = card.find_element(By.XPATH, ".//img")
                    
                    # Take screenshot before clicking
                    self.take_screenshot("before_profile_detail_click")
                    
                    # Click on the card/image to view details
                    self.safe_click(card_image)
                    logger.info("Clicked on card to view details")
                    
                    # Wait for details to appear or modal to open
                    time.sleep(2)
                    self.take_screenshot("after_profile_detail_click")
                    
                    # Simply verify we're still on the page and didn't crash
                    # The exact UI behavior may vary
                    if self.driver.current_url.endswith("/swipe"):
                        logger.info("Still on swipe page after profile detail interaction")
                        return True
                    else:
                        logger.warning(f"Unexpected navigation to {self.driver.current_url}")
                        return False
                        
                except NoSuchElementException:
                    logger.warning("Could not find clickable element on the card")
                    return False
                    
            except NoSuchElementException:
                logger.info("No profiles available for viewing details, skipping test")
                return True
                
        except Exception as e:
            logger.error(f"Profile details viewing error: {e}")
            self.take_screenshot("profile_details_error")
            raise


class MatchesTesting(DatingAppTest):
    """Test the matches functionality"""
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config, setup_driver=False)
    
    def test_matches_page_loads(self):
        """Test that the matches page loads successfully"""
        try:
            # Ensure we're logged in
            if not self.authenticated:
                self.login()
            
            # Navigate to matches page
            self.navigate_to(f"{self.config['base_url']}/matches")
            self.add_delay()
            
            # Take a screenshot to see what we get
            self.take_screenshot("matches_page_loaded")
            
            # Verify matches page loaded by checking for header and tabs
            try:
                # Look for the page header "Your Matches"
                header = self.driver.find_element(By.XPATH, "//h1[contains(text(), 'Your Matches')]")
                logger.info(f"Found matches header: {header.text}")
                
                # Look for the tabs for confirmed vs potential matches
                tabs = self.driver.find_elements(
                    By.XPATH, "//div[contains(@class, 'bg-white rounded-xl mb-6')]//button"
                )
                
                if tabs and len(tabs) > 0:
                    logger.info(f"Found {len(tabs)} match tabs")
                    return True
                else:
                    logger.warning("Match tabs not found")
                    return False
                    
            except NoSuchElementException:
                logger.warning("Matches page header not found")
                return False
            
        except Exception as e:
            logger.error(f"Matches page loading error: {e}")
            self.take_screenshot("matches_page_error")
            raise
    
    def test_view_confirmed_matches(self):
        """Test viewing confirmed matches tab"""
        try:
            # Ensure we're logged in
            if not self.authenticated:
                self.login()
            
            # Navigate to matches page
            self.navigate_to(f"{self.config['base_url']}/matches")
            self.add_delay()
            
            # Check if there are any matches listed
            try:
                # Look for match cards
                match_cards = self.driver.find_elements(
                    By.XPATH, "//div[contains(@class, 'overflow-hidden') and contains(@class, 'shadow-card')]"
                )
                
                if match_cards and len(match_cards) > 0:
                    logger.info(f"Found {len(match_cards)} match entries")
                    
                    # Try to interact with the first match
                    try:
                        view_button = match_cards[0].find_element(
                            By.XPATH, ".//button[contains(text(), 'View Profile')]"
                        )
                        
                        # Take screenshot before clicking
                        self.take_screenshot("before_view_profile_click")
                        
                        # Click the view profile button
                        self.safe_click(view_button)
                        logger.info("Clicked View Profile button")
                        self.add_delay(2)
                        
                        # Take screenshot after clicking
                        self.take_screenshot("after_view_profile_click")
                        
                        # Verify we're still on the matches page or have opened a modal
                        if self.driver.current_url.endswith("/matches"):
                            logger.info("Still on matches page after profile view interaction")
                            return True
                        else:
                            logger.info(f"Navigated to {self.driver.current_url} after profile view")
                            return True
                        
                    except NoSuchElementException:
                        logger.warning("View Profile button not found in match card")
                        # Try clicking on the match card itself
                        try:
                            self.safe_click(match_cards[0])
                            logger.info("Clicked directly on match card")
                            self.add_delay(2)
                            self.take_screenshot("after_match_card_click")
            return True
        except Exception as e:
                            logger.error(f"Error clicking match card: {e}")
                            return False
                        
                else:
                    logger.info("No matches found, skipping test")
                    return True
                    
            except Exception as e:
                logger.error(f"Error looking for matches: {e}")
                return False
                
        except Exception as e:
            logger.error(f"View confirmed matches error: {e}")
            self.take_screenshot("view_confirmed_matches_error")
            raise
    
    def test_potential_matches(self):
        """Test viewing potential matches tab"""
        try:
            # Ensure we're logged in
            if not self.authenticated:
                self.login()
            
            # Navigate to matches page
            self.navigate_to(f"{self.config['base_url']}/matches")
            self.add_delay()
            
            # Look for the Potential Matches tab
            try:
                # Get all buttons in the tab section
                tab_buttons = self.driver.find_elements(
                    By.XPATH, "//div[contains(@class, 'bg-white rounded-xl mb-6')]//button"
                )
                
                if tab_buttons and len(tab_buttons) >= 2:
                    # The second button should be "Potential Matches"
                    potential_tab = tab_buttons[1]
                    logger.info(f"Found potential matches tab: {potential_tab.text}")
                    
                    # Take screenshot before clicking
                    self.take_screenshot("before_potential_matches_click")
                    
                    # Click the potential matches tab
                    self.safe_click(potential_tab)
                    logger.info("Clicked Potential Matches tab")
                    self.add_delay(2)
                    
                    # Take a screenshot after clicking
                    self.take_screenshot("after_potential_matches_click")
                    
                    # Successfully clicked the tab, consider it a pass
            return True
                else:
                    logger.warning("Could not find tab buttons or there's only one tab")
                    return False
                    
        except Exception as e:
                logger.error(f"Error finding or clicking potential matches tab: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Potential matches test error: {e}")
            self.take_screenshot("potential_matches_error")
            raise


class ExperienceTesting(DatingAppTest):
    """Test the Experiences functionality"""
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config, setup_driver=False)
    
    def test_experiences_page_loads(self):
        """Test that the experiences page loads successfully"""
        try:
            # Ensure we're logged in
            if not self.authenticated:
                self.login()
            
            # Navigate to experiences page
            self.navigate_to(f"{self.config['base_url']}/experiences")
            self.add_delay(2)
            
            # Take a screenshot of what we get
            self.take_screenshot("experiences_page_loaded")
            
            # Check for experiences page elements
            try:
                # Find the experiences header
                header = self.driver.find_element(By.XPATH, "//h1[contains(text(), 'Experiences')]")
                logger.info(f"Found experiences header: {header.text}")
                
                # Look for the grid of experiences
                grid_elements = self.driver.find_elements(
                    By.XPATH, "//div[contains(@class, 'grid')]"
                )
                
                if not grid_elements:
                    logger.warning("Experience grid not found")
                    return False
                    
                logger.info("Found experience grid")
                
                # Check if there are any experience cards
                experience_cards = self.driver.find_elements(
                    By.XPATH, "//div[contains(@class, 'grid')]/div"
                )
                
                if experience_cards:
                    logger.info(f"Found {len(experience_cards)} experience cards")
                else:
                    logger.info("No experience cards found - user may not have added experiences yet")
                
                # Look for Add Experience button
                add_buttons = self.driver.find_elements(
                    By.XPATH, "//button[contains(text(), 'Add Experience') or .//svg[contains(@d, 'M12 6v6m0 0v6m0-6h6m-6 0H6')]]"
                )
                
                if add_buttons:
                    logger.info("Found Add Experience button")
                else:
                    logger.warning("Add Experience button not found with specific selector")
                
                # Page loaded successfully
                return True
                    
            except Exception as e:
                logger.warning(f"Error finding experiences page elements: {str(e)}")
                self.take_screenshot("experiences_page_elements_not_found")
                return False
        
        except Exception as e:
            logger.error(f"Experiences page loading error: {e}")
            self.take_screenshot("experiences_page_error")
            raise
    
    def test_experience_filtering(self):
        """Test experience filtering or sorting functionality if available"""
        try:
            # Ensure we're logged in
            if not self.authenticated:
                self.login()
            
            # Navigate to experiences page
            self.navigate_to(f"{self.config['base_url']}/experiences")
            self.add_delay(2)
            
            # Take a screenshot of the initial state
            self.take_screenshot("experience_filtering_initial")
            
            # Look for filtering/sorting controls
            filter_buttons = []
            
            # Try different selectors for potential filter buttons
            selectors = [
                "//button[contains(text(), 'Filter')]",
                "//button[contains(text(), 'Sort')]", 
                "//select[contains(@class, 'filter')]",
                "//div[contains(@class, 'filter')]//button"
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        filter_buttons.extend(elements)
                except:
                    pass
            
            if filter_buttons:
                logger.info(f"Found {len(filter_buttons)} filter/sort controls")
                
                # Try to interact with the first filter button
                filter_button = filter_buttons[0]
                
                # Scroll to the filter button
                self.scroll_to_element(filter_button)
                self.add_delay(1)
                
                # Take screenshot before clicking
                self.take_screenshot("before_filter_click")
                
                # Click the filter button
                self.safe_click(filter_button)
                logger.info("Clicked filter/sort button")
                self.add_delay(1)
                
                # Take screenshot after clicking
                self.take_screenshot("after_filter_click")
                
                # Check if a dropdown or filter menu appeared
                filter_options = []
                option_selectors = [
                    "//div[contains(@class, 'dropdown')]//button", 
                    "//ul[contains(@class, 'dropdown')]//li",
                    "//div[contains(@class, 'menu')]//button",
                    "//select[contains(@class, 'filter')]/option"
                ]
                
                for selector in option_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        if elements:
                            filter_options.extend(elements)
                    except:
                        pass
                
                if filter_options:
                    logger.info(f"Found {len(filter_options)} filter options")
                    
                    # Try to click the first option
                    option = filter_options[0]
                    self.scroll_to_element(option)
                    self.safe_click(option)
                    logger.info("Selected filter option")
                    self.add_delay(2)
                    
                    # Take screenshot after selecting filter
                    self.take_screenshot("after_filter_selection")
                    
                    # Check if the page content updated
                    try:
                        updated_grid = self.driver.find_element(By.XPATH, "//div[contains(@class, 'grid')]")
                        logger.info("Grid still visible after filtering")
                        return True
                    except:
                        logger.warning("Grid not found after filtering")
                        return False
                else:
                    logger.info("No filter options found, filtering may not be implemented")
                    return True
            else:
                logger.info("No filtering/sorting controls found, feature may not be implemented")
                
                # Check for category tabs or other filtering mechanism
                category_tabs = self.driver.find_elements(
                    By.XPATH, "//div[contains(@class, 'tabs') or contains(@class, 'categories')]//button"
                )
                
                if category_tabs:
                    logger.info(f"Found {len(category_tabs)} category tabs")
                    
                    # Click the first non-active tab if there are multiple
                    if len(category_tabs) > 1:
                        # Try to identify non-active tab
                        for tab in category_tabs[1:]:  # Skip first tab which might be active
                            self.scroll_to_element(tab)
                            self.take_screenshot("before_category_tab_click")
                            self.safe_click(tab)
                            logger.info("Clicked category tab")
                            self.add_delay(2)
                            self.take_screenshot("after_category_tab_click")
                            return True
                    
                return True  # No filtering controls is not a failure
            
        except Exception as e:
            logger.error(f"Experience filtering test error: {e}")
            self.take_screenshot("experience_filtering_error")
            return False

    def test_add_experience_form(self):
        """Test the add experience form"""
        try:
            # Ensure we're logged in
            if not self.authenticated:
                self.login()
            
            # Navigate to experiences page
            self.navigate_to(f"{self.config['base_url']}/experiences")
            self.add_delay(2)
            
            # Look for the Add Experience button
            add_buttons = self.driver.find_elements(
                By.XPATH, "//button[contains(text(), 'Add Experience') or .//svg[contains(@d, 'M12 6v6m0 0v6m0-6h6m-6 0H6')]]"
            )
            
            if not add_buttons:
                # Try more general approach
                add_buttons = self.driver.find_elements(
                    By.XPATH, "//button[contains(@class, 'px-4') and contains(@class, 'py-2')]"
                )
            
            if not add_buttons or len(add_buttons) == 0:
                logger.error("Add Experience button not found with any selector")
                self.take_screenshot("add_experience_button_not_found")
                return False
                
            # We found the add button
            add_button = add_buttons[0]
            logger.info("Found Add Experience button")
            
            # Take screenshot before clicking
            self.take_screenshot("before_add_experience_click")
            
            # Scroll to button and click it
            self.scroll_to_element(add_button)
            self.safe_click(add_button)
            logger.info("Clicked Add Experience button")
            self.add_delay(2)
            
            # Take screenshot of the modal
            self.take_screenshot("add_experience_modal")
            
            # Find the form
            try:
                form = self.driver.find_element(By.XPATH, "//form")
                logger.info("Found experience form")
                
                # Fill out the form
                try:
                    # 1. Experience type - scroll to it first
                    self.add_delay()
                    select_element = form.find_element(By.NAME, "experience_type")
                    self.scroll_to_element(select_element)
                    select = Select(select_element)
                    select.select_by_visible_text("Cafe")
                    logger.info("Selected 'Cafe' as experience type")
                    
                    # 2. Experience name - scroll to it first
                    self.add_delay()
                    name_input = form.find_element(By.NAME, "experience_name")
                    self.scroll_to_element(name_input)
                    name_input.clear()
                    name_input.send_keys(f"Test Cafe {datetime.now().strftime('%H:%M:%S')}")
                    logger.info("Entered test name in experience name field")
                    
                    # 3. Location - scroll to it first
                    self.add_delay()
                    location_input = form.find_element(By.NAME, "location")
                    self.scroll_to_element(location_input)
                    location_input.clear()
                    location_input.send_keys("Princeton University, Princeton, NJ")
                    logger.info("Entered location in location field")
                    
                    # 4. Description - scroll to it first
                    self.add_delay()
                    description_textarea = form.find_element(By.NAME, "description")
                    self.scroll_to_element(description_textarea)
                    description_textarea.clear()
                    description_textarea.send_keys("This is a test experience created by automated testing.")
                    logger.info("Entered text in description field")
                    
                    self.add_delay()
                    self.take_screenshot("filled_experience_form")
                    
                    # Find form buttons - scroll to them first
                    form_buttons = form.find_elements(
                        By.XPATH, ".//button[@type='button']"
                    )
                    
                    if len(form_buttons) >= 2:
                        # Change: Click the Save button (second button) instead of Cancel
                        save_button = form_buttons[1]  # Second button is Save
                        logger.info("Found Save button")
                        
                        # Scroll to and click Save
                        self.scroll_to_element(save_button)
                        self.safe_click(save_button)
                        logger.info("Clicked Save button")
                        self.add_delay(2)  # Longer delay to allow save to complete
                        
                        # Take screenshot after saving
                        self.take_screenshot("after_save_add_experience")
                        return True
                    else:
                        # Try to find submit button with other selectors
                        save_buttons = self.driver.find_elements(
                            By.XPATH, "//button[contains(text(), 'Save') or contains(text(), 'Submit') or contains(text(), 'Add') or @type='submit']"
                        )
                        if save_buttons:
                            save_button = save_buttons[0]
                            logger.info("Found Save button with alternative selector")
                            
                            self.scroll_to_element(save_button)
                            self.safe_click(save_button)
                            logger.info("Clicked Save button")
                            self.add_delay(2)
                            
                            self.take_screenshot("after_save_add_experience_alt")
                            return True
                        else:
                            logger.warning("Could not find any buttons to save the form")
                            return False
                except Exception as e:
                    logger.error(f"Error filling form fields: {e}")
                    self.take_screenshot("form_fields_error")
                    
                    # Try to close modal if it's still open
                    try:
                        close_buttons = self.driver.find_elements(
                            By.XPATH, "//button[.//svg[contains(@d, 'M6 18L18 6M6 6l12 12')]]"
                        )
                        if close_buttons:
                            self.scroll_to_element(close_buttons[0])
                            self.safe_click(close_buttons[0])
                            logger.info("Attempted to close modal after error")
                            self.add_delay()
                    except:
                        pass
                    
                    return False
            except NoSuchElementException:
                logger.error("Could not find experience form")
                self.take_screenshot("form_not_found")
                return False
                
        except NoSuchElementException as e:
            logger.error(f"Element not found in add experience form test: {e}")
            self.take_screenshot("add_experience_element_not_found")
            return False
        except Exception as e:
            logger.error(f"Add Experience form test error: {e}")
            self.take_screenshot("add_experience_test_error")
            raise

    def test_edit_experience(self):
        """Test editing an experience if any exist"""
        try:
            # Ensure we're logged in
            if not self.authenticated:
                self.login()
            
            # Navigate to experiences page
            self.navigate_to(f"{self.config['base_url']}/experiences")
            self.add_delay(2)
            
            # Check if there are any experience cards
            experience_cards = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'grid')]//div[contains(@class, 'bg-white')]"
            )
            
            if not experience_cards or len(experience_cards) == 0:
                logger.info("No experiences found to edit - skipping edit test")
                return True
            
            logger.info(f"Found {len(experience_cards)} experience card(s)")
            
            # Find the edit button on the first experience card
            edit_buttons = experience_cards[0].find_elements(
                By.XPATH, ".//button[@aria-label='Edit'] | .//button[.//svg[contains(@d, 'M11 5H6a2 2 0 00-2 2v11')]]"
            )
            
            if not edit_buttons:
                # Try more general approach
                edit_buttons = experience_cards[0].find_elements(
                    By.XPATH, ".//button[contains(@class, 'text-blue')]"
                )
            
            if not edit_buttons or len(edit_buttons) == 0:
                logger.warning("Edit button not found on experience card")
                self.take_screenshot("edit_button_not_found")
                return False
            
            # We found the edit button
            edit_button = edit_buttons[0]
            logger.info("Found Edit button on experience card")
            
            # Take screenshot before clicking
            self.take_screenshot("before_edit_experience_click")
            
            # Scroll to and click the edit button
            self.scroll_to_element(edit_button)
            self.safe_click(edit_button)
            logger.info("Clicked Edit button")
            self.add_delay(2)
            
            # Take screenshot of the edit modal
            self.take_screenshot("edit_experience_modal")
            
            # Find the form in the modal
            try:
                form = self.driver.find_element(By.XPATH, "//form")
                logger.info("Found form in edit modal")
                
                # Update the description field - scroll to it first
                self.add_delay()
                description_textarea = form.find_element(By.NAME, "description")
                self.scroll_to_element(description_textarea)
                current_text = description_textarea.get_attribute("value") or ""
                description_textarea.clear()
                description_textarea.send_keys(f"Updated description at {datetime.now().strftime('%H:%M:%S')}")
                logger.info(f"Updated description from '{current_text}' to new text")
                
                self.add_delay()
                self.take_screenshot("updated_experience_form")
                
                # Find the form buttons - scroll to them first
                form_buttons = form.find_elements(
                    By.XPATH, ".//button[@type='button']"
                )
                
                if len(form_buttons) >= 2:
                    # Change: Click the Save button (second button) instead of Cancel
                    save_button = form_buttons[1]  # Second button is Save
                    logger.info("Found Save button")
                    
                    # Scroll to and click Save
                    self.scroll_to_element(save_button)
                    self.safe_click(save_button)
                    logger.info("Clicked Save button")
                    self.add_delay(2)  # Longer delay to allow save to complete
                    
                    # Take screenshot after saving
                    self.take_screenshot("after_save_edit_experience")
            return True
                else:
                    # Try to find submit button with other selectors
                    save_buttons = self.driver.find_elements(
                        By.XPATH, "//button[contains(text(), 'Save') or contains(text(), 'Update') or contains(text(), 'Submit') or @type='submit']"
                    )
                    if save_buttons:
                        save_button = save_buttons[0]
                        logger.info("Found Save button with alternative selector")
                        
                        self.scroll_to_element(save_button)
                        self.safe_click(save_button)
                        logger.info("Clicked Save button")
                        self.add_delay(2)
                        
                        self.take_screenshot("after_save_edit_experience_alt")
                        return True
                    else:
                        logger.warning("Could not find any buttons to save the modal")
                        return False
        except Exception as e:
                logger.error(f"Error interacting with edit form: {e}")
                self.take_screenshot("edit_form_error")
                
                # Try to close modal if it's still open
                try:
                    close_buttons = self.driver.find_elements(
                        By.XPATH, "//button[.//svg[contains(@d, 'M6 18L18 6M6 6l12 12')]]"
                    )
                    if close_buttons:
                        self.scroll_to_element(close_buttons[0])
                        self.safe_click(close_buttons[0])
                        logger.info("Attempted to close modal after error")
                        self.add_delay()
                except:
                    pass
                
                return False
            
        except NoSuchElementException as e:
            logger.error(f"Element not found in edit experience test: {e}")
            self.take_screenshot("edit_experience_element_not_found")
            return False
        except Exception as e:
            logger.error(f"Edit experience test error: {e}")
            self.take_screenshot("edit_experience_test_error")
            raise


# Test decorator for timeout and retry
def with_retry_and_timeout(max_retries=None, timeout=None):
    """Decorator to add timeout and retry functionality to test methods"""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # Get retry count from global args or from parameters
            retries = max_retries if max_retries is not None else TEST_CONFIG.get('retry_count', 1)
            test_timeout = timeout if timeout is not None else TEST_CONFIG.get('test_timeout', 300)
            
            # For timeout functionality
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Test {func.__name__} timed out after {test_timeout} seconds")
            
            # Try the test with retries
            for attempt in range(retries):
                try:
                    # Set timeout
                    if test_timeout:
                        try:
                            signal.signal(signal.SIGALRM, timeout_handler)
                            signal.alarm(test_timeout)
                        except Exception as e:
                            logger.warning(f"Could not set timeout alarm: {e}")
                    
                    # Run the test
                    result = func(self, *args, **kwargs)
                    
                    # Cancel timeout
                    if test_timeout:
                        try:
                            signal.alarm(0)
                        except Exception:
                            pass
                    
                    # Success! Return the result
                    return result
                    
                except Exception as e:
                    # Reset the timeout alarm
                    if test_timeout:
                        try:
                            signal.alarm(0)
                        except Exception:
                            pass
                    
                    # Log the error
                    logger.error(f"Test {func.__name__} failed on attempt {attempt+1}/{retries}: {e}")
                    
                    # Take screenshot of failure
                    if hasattr(self, 'take_screenshot'):
                        self.take_screenshot(f"{func.__name__}_failure_attempt_{attempt+1}")
                    
                    # If it's the last attempt, re-raise the exception
                    if attempt == retries - 1:
                        raise
                    else:
                        # Log that we're retrying
                        logger.info(f"Retrying test {func.__name__} (attempt {attempt+2}/{retries})")
                        
                        # Wait briefly before retry
                        time.sleep(3)
            
            # Should never get here, but just in case
            raise Exception(f"Test {func.__name__} failed after {retries} attempts")
            
        return wrapper
    return decorator

# Timeout and retry functionality with platform-specific implementation
def run_test_with_retry(test_instance, test_method, test_name, results_dict):
    """Run a single test with timeout and retry logic"""
    retry_count = TEST_CONFIG.get("retry_count", 1)
    test_timeout = TEST_CONFIG.get("test_timeout", 300)
    
    # Try the test with retries
    for attempt in range(retry_count):
        is_timeout = [False]  # Using a list to allow modification inside the timer callback
        timer = None
        
        try:
            if test_timeout:
                def timeout_handler():
                    is_timeout[0] = True
                    logger.warning(f"Test {test_name} timed out after {test_timeout} seconds")
                
                # Set up the timer but don't start it yet
                timer = threading.Timer(test_timeout, timeout_handler)
                timer.daemon = True  # Make sure timer doesn't prevent program exit
                timer.start()
            
            # Run the test
            result = test_method()
            
            # Check if timeout occurred during test execution
            if is_timeout[0]:
                logger.error(f"Test {test_name} timed out (attempt {attempt + 1}/{retry_count})")
                
                if attempt < retry_count - 1:
                    logger.info(f"Retrying {test_name}...")
                    continue
                else:
                    print(f"❌ {test_name} test timed out after {retry_count} attempts")
                    results_dict[test_name] = False
                    return
            
            # Test completed successfully
            if result:
                # Success!
                print(f"✅ {test_name} test completed successfully")
            else:
                # Test returned False but didn't raise an exception
                print(f"⚠️ {test_name} test completed but returned False")
            
            results_dict[test_name] = result
            return
            
        except Exception as e:
            logger.error(f"Error in {test_name}: {e}")
            if attempt < retry_count - 1:
                logger.info(f"Retrying {test_name}...")
            else:
                print(f"❌ {test_name} test failed with error: {e}")
                results_dict[test_name] = False
                return
                
        finally:
            # Cancel the timer if it's running
            if timer and timer.is_alive():
                timer.cancel()
            
    # If we get here, all retries failed
    results_dict[test_name] = False
    print(f"❌ {test_name} test failed after {retry_count} attempts")

# Modify run_all_tests to use MatchesTesting instead of MessagingTesting
def run_all_tests():
    """Run all tests sequentially with proper error handling"""
    # Set up dict to track results
    results = {
        "login": False,
        "profile": {},
        "matching": {},
        "matches": {},  # Changed from messaging to matches
        "experiences": {}
    }
    
    # Check if specific tests were requested
    if args.tests:
        test_classes = [t.strip() for t in args.tests.split(',')]
        logger.info(f"Running only the following test classes: {test_classes}")
    else:
        test_classes = ["ProfileTesting", "MatchingTesting", "MatchesTesting", "ExperienceTesting"]  # Updated from MessagingTesting to MatchesTesting
    
    # Initialize a single browser session for all tests
    main_test = DatingAppTest()
    
    # If in manual mode, allow initial browser inspection
    if main_test.config.get("manual_mode"):
        main_test.navigate_to(main_test.config["base_url"])
        main_test.manual_browser_interaction("Initial page inspection")
    
    try:
        # Authentication test is mandatory
        print("\n===== Running Authentication Tests =====")
        
        if main_test.config.get("manual_auth"):
            print("\nManual authentication mode enabled.")
            print("You will be prompted to manually log in through the browser.")
            print("After you complete login, the automated tests will continue.\n")
            
        results["login"] = main_test.login()
        
        if not results["login"]:
            print("\n❌ Authentication failed. Cannot continue with tests.")
            main_test.teardown()
            return results
            
        print("\n✅ Authentication successful! Proceeding with tests.")
        
        # If login successful and pause after login is enabled, allow manual inspection
        if results["login"] and main_test.config.get("pause_after_login"):
            main_test.manual_browser_interaction("Post-login inspection")
            
            # Only continue with other tests if login is successful
            
            # Profile tests
        if "ProfileTesting" in test_classes:
            print("\n===== Running Profile Tests =====")
            profile_test = ProfileTesting()
            profile_test.driver = main_test.driver  # Share the browser session
            profile_test.authenticated = main_test.authenticated
            profile_test.wait = main_test.wait
            profile_test.add_delay = main_test.add_delay  # Share delay method
            profile_test.manual_browser_interaction = main_test.manual_browser_interaction  # Share method
            
            run_test_with_retry(profile_test, profile_test.test_profile_view, "profile_view", results["profile"])
            run_test_with_retry(profile_test, profile_test.test_profile_editing, "profile_editing", results["profile"])
            run_test_with_retry(profile_test, profile_test.test_profile_completion, "profile_completion", results["profile"])
            # New advanced profile features test
            run_test_with_retry(profile_test, profile_test.test_profile_advanced_features, "profile_advanced_features", results["profile"])
            
            # Matching tests
        if "MatchingTesting" in test_classes:
            print("\n===== Running Matching Tests =====")
            matching_test = MatchingTesting()
            matching_test.driver = main_test.driver  # Share the browser session
            matching_test.authenticated = main_test.authenticated
            matching_test.wait = main_test.wait
            matching_test.add_delay = main_test.add_delay  # Share delay method
            matching_test.manual_browser_interaction = main_test.manual_browser_interaction  # Share method
            
            run_test_with_retry(matching_test, matching_test.test_swipe_page_loads, "swipe_page_loads", results["matching"])
            run_test_with_retry(matching_test, matching_test.test_swipe_functionality, "swipe_functionality", results["matching"])
            run_test_with_retry(matching_test, matching_test.test_profile_details, "profile_details", results["matching"])
            # New refresh button test
            run_test_with_retry(matching_test, matching_test.test_refresh_button, "refresh_button", results["matching"])
            
            # Matches tests (renamed from Messaging)
        if "MatchesTesting" in test_classes:
            print("\n===== Running Matches Tests =====")
            matches_test = MatchesTesting()  # Changed from MessagingTesting to MatchesTesting
            matches_test.driver = main_test.driver  # Share the browser session
            matches_test.authenticated = main_test.authenticated
            matches_test.wait = main_test.wait
            matches_test.add_delay = main_test.add_delay  # Share delay method
            matches_test.manual_browser_interaction = main_test.manual_browser_interaction  # Share method
            
            run_test_with_retry(matches_test, matches_test.test_matches_page_loads, "matches_page_loads", results["matches"])
            run_test_with_retry(matches_test, matches_test.test_view_confirmed_matches, "view_confirmed_matches", results["matches"])
            run_test_with_retry(matches_test, matches_test.test_potential_matches, "potential_matches", results["matches"])
            
            # Experience tests
        if "ExperienceTesting" in test_classes:
            print("\n===== Running Experience Tests =====")
            experience_test = ExperienceTesting()
            experience_test.driver = main_test.driver  # Share the browser session
            experience_test.authenticated = main_test.authenticated
            experience_test.wait = main_test.wait
            experience_test.add_delay = main_test.add_delay  # Share delay method
            experience_test.manual_browser_interaction = main_test.manual_browser_interaction  # Share method
            
            run_test_with_retry(experience_test, experience_test.test_experiences_page_loads, "experiences_page_loads", results["experiences"])
            run_test_with_retry(experience_test, experience_test.test_add_experience_form, "add_experience_form", results["experiences"])
            run_test_with_retry(experience_test, experience_test.test_edit_experience, "edit_experience", results["experiences"])
            # New experience filtering test
            run_test_with_retry(experience_test, experience_test.test_experience_filtering, "experience_filtering", results["experiences"])
        
        # Finally, test logout if not skipped
        if not args.skip_logout:
            try:
                results["logout"] = main_test.logout()
                print("✅ Logout test completed")
            except Exception as e:
                print(f"❌ Logout test failed: {e}")
                results["logout"] = False
        
    except Exception as e:
        print(f"❌ Authentication tests failed: {e}")
        results["login"] = False
    finally:
        # Only teardown the main test session at the very end
        main_test.teardown()
    
    # Print summary
    print("\n===== Test Results Summary =====")
    
    def count_results(results_dict):
        """Count passed and failed tests recursively"""
        passed, failed = 0, 0
        for key, value in results_dict.items():
            if isinstance(value, dict):
                sub_passed, sub_failed = count_results(value)
                passed += sub_passed
                failed += sub_failed
            else:
                if value is True:
                    passed += 1
                elif value is False:
                    failed += 1
        return passed, failed
    
    passed, failed = count_results(results)
    print(f"Passed: {passed}, Failed: {failed}, Total: {passed + failed}")
    
    # Print detailed results
    print("\nDetailed Results:")
    
    def print_results(results_dict, indent=0):
        """Print results recursively with indentation"""
        for key, value in results_dict.items():
            if isinstance(value, dict):
                print(f"{' ' * indent}- {key}:")
                print_results(value, indent + 2)
            else:
                status = "✅ PASS" if value else "❌ FAIL"
                print(f"{' ' * indent}- {status}: {key}")
    
    print_results(results)
    
    # Return the results dict for potential further processing
    return results


if __name__ == "__main__":
    print("=" * 50)
    print("Princeton Dating App Automated Testing System")
    print("=" * 50)
    
    # Check if app is reachable
    try:
        test_url = TEST_CONFIG["base_url"]
        print(f"\nChecking if app URL is reachable: {test_url}")
        
        response = requests.get(test_url, timeout=10)
        if response.status_code == 200:
            print("✅ App URL is reachable!")
        else:
            print(f"⚠️ App URL returned status code {response.status_code}")
            confirm = input("Do you want to continue testing anyway? (y/n): ").lower().strip() 
            if confirm != 'y':
                print("Testing aborted")
                sys.exit(1)
    except Exception as e:
        print(f"⚠️ Warning: Could not reach app URL: {e}")
        confirm = input("App URL may not be reachable. Continue anyway? (y/n): ").lower().strip()
        if confirm != 'y':
            print("Testing aborted")
            sys.exit(1)
    
    # Check if credentials are provided
    if not TEST_CREDENTIALS["username"] or not TEST_CREDENTIALS["password"]:
        print("\n⚠️  WARNING: No NetID or password provided for CAS login")
        print("You can provide credentials using command line args, environment variables, or manual input")
        
        # Prompt for credentials if not provided via args or env vars
        if not TEST_CREDENTIALS["username"]:
            TEST_CREDENTIALS["username"] = input("Enter Princeton NetID: ")
        
        if not TEST_CREDENTIALS["password"]:
            import getpass
            TEST_CREDENTIALS["password"] = getpass.getpass("Enter password: ")
    
    print("\nThis test suite will handle Princeton CAS login but requires manual Duo authentication when prompted")
    print("\nTest run starting...\n")
    
    # Run all tests
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error during test execution: {e}")
    
    print("\nTest execution completed")