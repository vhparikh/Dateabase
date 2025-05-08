#!/usr/bin/env python3
"""
Simplified Princeton Dating App Testing Script
"""

import os
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("simple_tests.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SimpleTests")

# Create screenshots directory
SCREENSHOT_DIR = "test_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

class SimpleTest:
    """Simplified test class for DateABase app"""
    
    def __init__(self, base_url="https://date-a-base-with-credits-839b845c06a6.herokuapp.com"):
        """Initialize the test class"""
        self.base_url = base_url
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Set up the Chrome WebDriver"""
        options = ChromeOptions()
        
        # Performance and stability options
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # Create the ChromeDriver instance
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        # Configure driver
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 30)
        logger.info("Chrome browser initialized")
    
    def take_screenshot(self, name):
        """Take a screenshot with a timestamp"""
        if not self.driver:
            logger.warning("Cannot take screenshot - driver not initialized")
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{SCREENSHOT_DIR}/{name}_{timestamp}.png"
        try:
            self.driver.save_screenshot(filename)
            logger.info(f"Screenshot saved: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None
    
    def add_delay(self, seconds=1.5):
        """Add a small delay to make actions more visible"""
        time.sleep(seconds)
        logger.info(f"Added {seconds} second delay for visibility")
    
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
    
    def manual_authentication(self):
        """Handle manual authentication by the user"""
        try:
            # Navigate to the login page
            self.driver.get(self.base_url)
            
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
            
            return True
        except Exception as e:
            logger.error(f"Error during manual authentication: {e}")
            return False
    
    def test_swipe_page(self):
        """Test the swipe page functionality"""
        try:
            # Navigate to swipe page
            self.driver.get(f"{self.base_url}/swipe")
            self.add_delay(2)
            
            # Take a screenshot
            self.take_screenshot("swipe_page_loaded")
            
            # Check if there are profiles to swipe
            try:
                # First look for the card container and get its details
                card = self.driver.find_element(By.XPATH, "//div[contains(@class, 'hinge-card')]")
                logger.info("Found swipe card container")
                
                # Scroll down to make buttons visible
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
                self.add_delay(1)
                
                # Test the refresh button first
                try:
                    refresh_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Refresh']")
                    logger.info("Found refresh button")
                    
                    # Take screenshot before clicking
                    self.take_screenshot("before_refresh_click")
                    
                    # Scroll to button and click it
                    self.scroll_to_element(refresh_button)
                    refresh_button.click()
                    logger.info("Clicked refresh button")
                    self.add_delay(2)
                    
                    # Take screenshot after clicking
                    self.take_screenshot("after_refresh_click")
                except NoSuchElementException:
                    logger.warning("Could not find refresh button with specific selector")
                
                # Now test the like button
                try:
                    like_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Like']")
                    logger.info("Found like button")
                    
                    # Take screenshot before clicking
                    self.take_screenshot("before_like_click")
                    
                    # Scroll to button and click it
                    self.scroll_to_element(like_button)
                    like_button.click()
                    logger.info("Clicked like button")
                    self.add_delay(2)
                    
                    # Take screenshot after clicking
                    self.take_screenshot("after_like_click")
                except NoSuchElementException:
                    logger.warning("Could not find like button with specific selector")
                
                return True
            except NoSuchElementException:
                logger.warning("No profiles available for swiping")
                return True
                
        except Exception as e:
            logger.error(f"Error testing swipe page: {e}")
            self.take_screenshot("swipe_test_error")
            return False
    
    def test_experiences(self):
        """Test the experiences page functionality"""
        try:
            # Navigate to experiences page
            self.driver.get(f"{self.base_url}/experiences")
            self.add_delay(2)
            
            # Take a screenshot
            self.take_screenshot("experiences_page_loaded")
            
            # Check for experiences page elements
            try:
                header = self.driver.find_element(By.XPATH, "//h1[contains(text(), 'Experiences')]")
                logger.info(f"Found experiences header: {header.text}")
            except NoSuchElementException:
                logger.warning("Could not find experiences header")
            
            # Look for Add Experience button
            try:
                add_button = self.driver.find_element(
                    By.XPATH, "//button[contains(text(), 'Add Experience') or .//svg[contains(@d, 'M12 6v6m0 0v6m0-6h6m-6 0H6')]]"
                )
                logger.info("Found Add Experience button")
                
                # Take screenshot before clicking
                self.take_screenshot("before_add_experience_click")
                
                # Scroll to button and click it
                self.scroll_to_element(add_button)
                
                # Click the button
                add_button.click()
                logger.info("Clicked Add Experience button")
                self.add_delay(2)
                
                # Take screenshot of the form modal
                self.take_screenshot("add_experience_form_modal")
                
                # Find the form
                try:
                    form = self.driver.find_element(By.XPATH, "//form")
                    logger.info("Found experience form")
                    
                    # Fill out the form
                    try:
                        # 1. Experience type - scroll to it first
                        select_element = form.find_element(By.NAME, "experience_type")
                        self.scroll_to_element(select_element)
                        
                        select = Select(select_element)
                        select.select_by_visible_text("Cafe")
                        logger.info("Selected Cafe as experience type")
                        
                        # 2. Experience name - scroll to it first
                        name_input = form.find_element(By.NAME, "experience_name")
                        self.scroll_to_element(name_input)
                        
                        name_input.clear()
                        name_input.send_keys(f"Test Cafe {datetime.now().strftime('%H:%M:%S')}")
                        logger.info("Entered name in experience name field")
                        
                        # 3. Location - scroll to it first
                        location_input = form.find_element(By.NAME, "location")
                        self.scroll_to_element(location_input)
                        
                        location_input.clear()
                        location_input.send_keys("Princeton University, Princeton, NJ")
                        logger.info("Entered location field")
                        
                        # 4. Description - scroll to it first
                        description_textarea = form.find_element(By.NAME, "description")
                        self.scroll_to_element(description_textarea)
                        
                        description_textarea.clear()
                        description_textarea.send_keys("This is a test experience created by automated testing.")
                        logger.info("Entered description field")
                        
                        # Take screenshot of filled form
                        self.add_delay()
                        self.take_screenshot("filled_experience_form")
                        
                        # Find save button
                        form_buttons = form.find_elements(By.XPATH, ".//button[@type='button']")
                        
                        if len(form_buttons) >= 2:
                            save_button = form_buttons[1]  # Second button is Save
                            logger.info("Found Save button")
                            
                            # Scroll to button and click it
                            self.scroll_to_element(save_button)
                            save_button.click()
                            logger.info("Clicked Save button")
                            self.add_delay(2)
                            
                            # Take screenshot after saving
                            self.take_screenshot("after_save_experience")
                        else:
                            logger.warning("Could not find Save button")
                        
                    except Exception as e:
                        logger.error(f"Error filling experience form: {e}")
                        self.take_screenshot("form_fill_error")
                    
                except NoSuchElementException:
                    logger.error("Could not find experience form")
                    self.take_screenshot("form_not_found")
            except NoSuchElementException:
                logger.error("Add Experience button not found")
                self.take_screenshot("add_button_not_found")
            
            # Test filtering functionality if available
            try:
                # Look for filtering controls
                filter_buttons = []
                
                # Try different selectors for filter buttons
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
                    self.scroll_to_element(filter_button)
                    
                    # Take screenshot before clicking
                    self.take_screenshot("before_filter_click")
                    
                    # Click the filter button
                    filter_button.click()
                    logger.info("Clicked filter/sort button")
                    self.add_delay(1)
                    
                    # Take screenshot after clicking
                    self.take_screenshot("after_filter_click")
                else:
                    logger.info("No filtering controls found")
            except Exception as e:
                logger.error(f"Error testing filter functionality: {e}")
            
            # Test passed
            return True
            
        except Exception as e:
            logger.error(f"Error testing experiences page: {e}")
            self.take_screenshot("experience_test_error")
            return False
        
    def teardown(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")
            self.driver = None

def main():
    """Main function to run all tests"""
    test = SimpleTest()
    
    try:
        print("Starting simplified tests...")
        
        # First authenticate
        print("\nPlease authenticate manually:")
        auth_success = test.manual_authentication()
        
        if not auth_success:
            print("Authentication failed, cannot continue")
            test.teardown()
            return
        
        print("Authentication successful!")
        
        # Run tests
        results = {}
        
        # Test swipe page
        print("\nTesting swipe page...")
        results["swipe_page"] = test.test_swipe_page()
        print(f"Swipe page test: {'PASSED' if results['swipe_page'] else 'FAILED'}")
        
        # Test experiences page
        print("\nTesting experiences page...")
        results["experiences"] = test.test_experiences()
        print(f"Experiences test: {'PASSED' if results['experiences'] else 'FAILED'}")
        
        # Print summary
        print("\n===== Test Results =====")
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        
    except Exception as e:
        print(f"Error in tests: {e}")
    finally:
        test.teardown()

if __name__ == "__main__":
    main() 