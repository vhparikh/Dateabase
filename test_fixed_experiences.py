#!/usr/bin/env python3
"""
Test script using the fixed ExperienceTesting class
"""

import os
import logging
import argparse
from pathlib import Path
from dating_app_test import DatingAppTest
from fixed_experience_testing import ExperienceTesting

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fixed_experience_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FixedExperienceTest")

# Parse command line arguments
parser = argparse.ArgumentParser(description='Run fixed Experience tests')
parser.add_argument('--manual-auth', action='store_true', help='Enable manual authentication')
args = parser.parse_args()

# Test configuration
TEST_CONFIG = {
    "base_url": "https://date-a-base-with-credits-839b845c06a6.herokuapp.com",
    "api_url": "https://date-a-base-with-credits-839b845c06a6.herokuapp.com/api",
    "headless": False,
    "timeout": 30,
    "screenshot_dir": "test_screenshots",
    "wait_for_duo": 60,
    "browser_window_size": (1920, 1080),
    "manual_auth": args.manual_auth,
}

# Create screenshot directory
Path(TEST_CONFIG["screenshot_dir"]).mkdir(parents=True, exist_ok=True)

def run_experience_tests():
    """Run the fixed Experience page tests"""
    print("\n" + "=" * 50)
    print("Fixed Experience Tests")
    print("=" * 50)
    
    # Initialize main test instance for browser setup and login
    main_test = DatingAppTest(TEST_CONFIG)
    
    try:
        # Handle login
        print("\nPerforming authentication...")
        login_success = main_test.login()
        
        if not login_success:
            print("\n❌ Authentication failed. Cannot continue with tests.")
            main_test.teardown()
            return False
        
        print("\n✅ Authentication successful! Proceeding with tests.")
        
        # Initialize the fixed experience testing class with the existing session
        experience_test = ExperienceTesting()
        experience_test.setup_with_session(
            driver=main_test.driver,
            wait=main_test.wait,
            authenticated=main_test.authenticated,
            config=main_test.config
        )
        
        # Dictionary to track test results
        results = {}
        
        # Run the tests
        print("\n===== Running Experience Tests =====")
        
        # Test 1: Experiences page loads
        try:
            print("\nTesting if experiences page loads correctly...")
            result = experience_test.test_experiences_page_loads()
            results["experiences_page_loads"] = "✅ PASS" if result else "❌ FAIL"
            print(f"Experiences page load: {results['experiences_page_loads']}")
        except Exception as e:
            logger.error(f"Error in experiences page load test: {e}")
            results["experiences_page_loads"] = "❌ FAIL (Exception)"
            print(f"Experiences page load: {results['experiences_page_loads']}")
        
        # Test 2: Add experience form
        try:
            print("\nTesting add experience form...")
            result = experience_test.test_add_experience_form()
            results["add_experience_form"] = "✅ PASS" if result else "❌ FAIL"
            print(f"Add experience form: {results['add_experience_form']}")
        except Exception as e:
            logger.error(f"Error in add experience form test: {e}")
            results["add_experience_form"] = "❌ FAIL (Exception)"
            print(f"Add experience form: {results['add_experience_form']}")
        
        # Test 3: Edit experience
        try:
            print("\nTesting edit experience functionality...")
            result = experience_test.test_edit_experience()
            results["edit_experience"] = "✅ PASS" if result else "❌ FAIL"
            print(f"Edit experience: {results['edit_experience']}")
        except Exception as e:
            logger.error(f"Error in edit experience test: {e}")
            results["edit_experience"] = "❌ FAIL (Exception)"
            print(f"Edit experience: {results['edit_experience']}")
        
        # Summary
        print("\n===== Test Results Summary =====")
        for test_name, status in results.items():
            print(f"{test_name}: {status}")
        
        # Count passes and fails
        passes = sum(1 for status in results.values() if "PASS" in status)
        fails = sum(1 for status in results.values() if "FAIL" in status)
        
        print(f"\nPassed: {passes}, Failed: {fails}, Total: {len(results)}")
        
        return passes == len(results)  # Return True if all tests passed
    
    except Exception as e:
        logger.error(f"Unexpected error in tests: {e}")
        print(f"\n❌ Unexpected error: {e}")
        return False
        
    finally:
        # Logout and cleanup
        if main_test.authenticated:
            try:
                main_test.logout()
                print("\nLogged out successfully")
            except Exception as e:
                logger.warning(f"Error during logout: {e}")
                print(f"\nWarning: Could not log out properly: {e}")
        
        # Close the browser
        main_test.teardown()
        print("\nTest session completed")

if __name__ == "__main__":
    success = run_experience_tests()
    exit(0 if success else 1) 