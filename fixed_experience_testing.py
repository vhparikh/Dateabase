#!/usr/bin/env python3
"""
Fixed ExperienceTesting class for dating app test
Import this and use it to replace the original ExperienceTesting class
"""

from typing import Dict, Any
from datetime import datetime
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException

logger = logging.getLogger("DatingAppTest")

class ExperienceTesting:
    """Test the Experiences functionality"""
    def __init__(self, config: Dict[str, Any] = None, setup_driver=False):
        from dating_app_test import DatingAppTest
        # Create empty parent class since we're using this as a drop-in replacement
        self.parent = DatingAppTest(config, setup_driver)
        self.driver = None
        self.wait = None
        self.authenticated = False
        self.config = config or {}
    
    def setup_with_session(self, driver, wait, authenticated, config):
        """Set up this test class with an existing session"""
        self.driver = driver
        self.wait = wait
        self.authenticated = authenticated
        self.config = config
        return self
    
    def take_screenshot(self, name):
        """Take a screenshot - delegate to parent object"""
        if hasattr(self, 'parent') and self.parent.driver:
            return self.parent.take_screenshot(name)
        
        # If driver is assigned directly
        if self.driver:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.config.get('screenshot_dir', 'test_screenshots')}/{name}_{timestamp}.png"
            try:
                self.driver.save_screenshot(filename)
                logger.info(f"Screenshot saved: {filename}")
                return filename
            except Exception as e:
                logger.error(f"Error taking screenshot: {e}")
                return None
    
    def navigate_to(self, url):
        """Navigate to a URL - delegate to parent object"""
        if hasattr(self, 'parent') and self.parent.driver:
            return self.parent.navigate_to(url)
        
        # If driver is assigned directly
        if self.driver:
            logger.info(f"Navigating to {url}")
            self.driver.get(url)
            return True
    
    def login(self):
        """Login - delegate to parent object"""
        if hasattr(self, 'parent') and self.parent.driver:
            return self.parent.login()
    
    def safe_click(self, element):
        """Safe click - delegate to parent object"""
        if hasattr(self, 'parent') and self.parent.driver:
            return self.parent.safe_click(element)
        
        # If driver is assigned directly
        if self.driver and element:
            element.click()
            return True
    
    def add_delay(self, seconds=1.5):
        """Add a small delay to make actions more visible"""
        time.sleep(seconds)
        logger.info(f"Added {seconds} second delay for visibility")
    
    def scroll_to_element(self, element):
        """Scroll the element into view with JavaScript"""
        try:
            if self.driver:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
                self.add_delay(0.5)  # Short delay to allow smooth scrolling
                logger.info("Scrolled element into view")
                return True
            elif hasattr(self, 'parent') and self.parent.driver:
                self.parent.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
                self.add_delay(0.5)
                logger.info("Scrolled element into view")
                return True
        except Exception as e:
            logger.warning(f"Error scrolling to element: {e}")
            return False
    
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
                
                if grid_elements:
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
                else:
                    logger.warning("Experience grid not found")
                    return False
                
            except Exception as e:
                logger.warning(f"Error finding experiences page elements: {str(e)}")
                self.take_screenshot("experiences_page_elements_not_found")
                return False
        
        except Exception as e:
            logger.error(f"Experiences page loading error: {e}")
            self.take_screenshot("experiences_page_error")
            raise
    
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
            
            if add_buttons:
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
                            # Use the Save button (second button) instead of Cancel
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
            else:
                logger.error("Add Experience button not found with any selector")
                self.take_screenshot("add_experience_button_not_found")
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
            
            if not experience_cards:
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
            
            if edit_buttons:
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
                        # Use the Save button (second button) instead of Cancel
                        save_button = form_buttons[1]  # Second button is Save
                        logger.info("Found Save button")
                        
                        # Scroll to save button and click
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
            else:
                logger.warning("Edit button not found on experience card")
                self.take_screenshot("edit_button_not_found")
                return False
            
        except NoSuchElementException as e:
            logger.error(f"Element not found in edit experience test: {e}")
            self.take_screenshot("edit_experience_element_not_found")
            return False
        except Exception as e:
            logger.error(f"Edit experience test error: {e}")
            self.take_screenshot("edit_experience_test_error")
            raise 