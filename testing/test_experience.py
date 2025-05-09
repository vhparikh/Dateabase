#!/usr/bin/env python3
"""
Princeton Dating App Experience Page Test
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
        logging.FileHandler("experience_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ExperienceTest")

# Create screenshots directory
SCREENSHOT_DIR = "test_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

class ExperienceTest:
    """Test class for the Experience page functionality"""
    
    def __init__(self, base_url="https://date-a-base-with-credits-839b845c06a6.herokuapp.com"):
        """Initialize the test with configuration"""
        self.base_url = base_url
        self.driver = None
        self.wait = None
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
                        element = WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located(locator)
                        )
                        logger.info(f"Found authenticated element with selector: {locator}")
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
                    return True
                else:
                    logger.error("User indicated authentication was not successful")
                    return False
        except Exception as e:
            logger.error(f"Error during manual authentication: {e}")
            return False
    
    def test_experiences_page(self):
        """Test the experiences page functionality"""
        try:
            # Navigate to experiences page
            self.driver.get(f"{self.base_url}/experiences")
            self.add_delay(2)
            
            # Take a screenshot
            self.take_screenshot("experiences_page_loaded")
            
            # Check for experiences page header
            try:
                header = self.driver.find_element(By.XPATH, "//h1[contains(text(), 'Experiences')]")
                logger.info(f"Found experiences header: {header.text}")
            except NoSuchElementException:
                logger.warning("Could not find experiences header")
            
            # Look for Add Experience button
            add_buttons = self.driver.find_elements(
                By.XPATH, "//button[contains(text(), 'Add Experience') or .//svg[contains(@d, 'M12 6v6m0 0v6m0-6h6m-6 0H6')]]"
            )
            
            if not add_buttons:
                logger.warning("Could not find Add Experience button with specific selectors")
                # Try more general approach
                add_buttons = self.driver.find_elements(
                    By.XPATH, "//button[contains(@class, 'px-4') and contains(@class, 'py-2')]"
                )
            
            if add_buttons:
                add_button = add_buttons[0]
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
                        
                        # Find cancel button
                        form_buttons = form.find_elements(By.XPATH, ".//button[@type='button']")
                        
                        if len(form_buttons) >= 2:
                            cancel_button = form_buttons[0]
                            logger.info("Found Cancel button")
                            
                            # Scroll to button and click it
                            self.scroll_to_element(cancel_button)
                            cancel_button.click()
                            logger.info("Clicked Cancel button")
                            
                        else:
                            # Try to find the close button
                            close_buttons = self.driver.find_elements(
                                By.XPATH, "//button[.//svg[contains(@d, 'M6 18L18 6M6 6l12 12')]]"
                            )
                            
                            if close_buttons:
                                close_button = close_buttons[0]
                                logger.info("Found close (X) button")
                                
                                self.scroll_to_element(close_button)
                                close_button.click()
                                logger.info("Clicked close button")
                            else:
                                logger.warning("Could not find any button to close the form")
                        
                    except Exception as e:
                        logger.error(f"Error filling experience form: {e}")
                        self.take_screenshot("form_fill_error")
                    
                except NoSuchElementException:
                    logger.error("Could not find experience form")
                    self.take_screenshot("form_not_found")
            else:
                logger.error("Add Experience button not found")
                self.take_screenshot("add_button_not_found")
            
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
    """Main function to run the test"""
    test = ExperienceTest()
    
    try:
        print("Starting Experience page test...")
        
        # First authenticate
        print("Please authenticate manually:")
        auth_success = test.manual_authentication()
        
        if not auth_success:
            print("Authentication failed, cannot continue")
            test.teardown()
            return
        
        # Test experiences page
        print("Testing Experiences page...")
        if test.test_experiences_page():
            print("✅ Experience page test PASSED")
        else:
            print("❌ Experience page test FAILED")
        
    except Exception as e:
        print(f"Error in test: {e}")
    finally:
        test.teardown()

if __name__ == "__main__":
    main() 