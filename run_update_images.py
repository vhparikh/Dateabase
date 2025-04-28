#!/usr/bin/env python3
"""
Wrapper script to run the experience image update script on Heroku.
This script will:
1. Push the update_images_script.py to Heroku
2. Run the script on Heroku to update experience images
"""

import os
import sys
import subprocess
import time

# Heroku app name
HEROKU_APP_NAME = "date-a-base-with-credits"

def run_command(command, description=None):
    """
    Run a shell command and print its output.
    
    Args:
        command (str): Command to run
        description (str, optional): Description of what the command does
        
    Returns:
        bool: True if command succeeded, False otherwise
    """
    if description:
        print(f"\n--- {description} ---")
    
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, 
                               capture_output=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        print(f"Exit code: {e.returncode}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False

def check_heroku_cli():
    """Check if Heroku CLI is installed and user is logged in."""
    print("Checking Heroku CLI installation...")
    
    # Check if heroku command exists
    if not run_command("heroku --version", "Checking Heroku CLI version"):
        print("Error: Heroku CLI is not installed. Please install it first.")
        print("Visit https://devcenter.heroku.com/articles/heroku-cli for installation instructions.")
        return False
    
    # Check if user is logged in
    if not run_command("heroku auth:whoami", "Checking Heroku authentication"):
        print("Error: Not logged into Heroku. Please run 'heroku login' first.")
        return False
    
    return True

def check_app_access():
    """Check if the user has access to the specified Heroku app."""
    print(f"Checking access to Heroku app: {HEROKU_APP_NAME}...")
    
    if not run_command(f"heroku apps:info -a {HEROKU_APP_NAME}", "Checking app info"):
        print(f"Error: Cannot access Heroku app '{HEROKU_APP_NAME}'.")
        print("Make sure the app exists and you have access to it.")
        return False
    
    return True

def push_script_to_heroku():
    """Copy the update script to Heroku."""
    print("Pushing update_images_script.py to Heroku...")
    
    # Verify the script exists
    if not os.path.exists("update_images_script.py"):
        print("Error: update_images_script.py not found in the current directory.")
        return False
    
    # Copy the script to Heroku using sftp plugin
    if not run_command(f"heroku ps:copy update_images_script.py -a {HEROKU_APP_NAME}", 
                      "Copying script to Heroku"):
        print("Error: Failed to copy script to Heroku.")
        print("Make sure the heroku-ps-copy plugin is installed.")
        print("You can install it with: heroku plugins:install heroku-ps-copy")
        return False
    
    return True

def run_script_on_heroku():
    """Run the update script on Heroku."""
    print("Running update_images_script.py on Heroku...")
    
    # Run the script on Heroku
    if not run_command(f"heroku run python update_images_script.py -a {HEROKU_APP_NAME}", 
                      "Running script on Heroku"):
        print("Error: Failed to run script on Heroku.")
        return False
    
    return True

def main():
    """Main function to run the update process."""
    print("\n==== Experience Image Update Process ====\n")
    
    # Check prerequisites
    if not check_heroku_cli():
        sys.exit(1)
    
    if not check_app_access():
        sys.exit(1)
    
    # Push and run script
    if not push_script_to_heroku():
        sys.exit(1)
    
    if not run_script_on_heroku():
        sys.exit(1)
    
    print("\n==== Experience Image Update Process Completed ====\n")
    print("All images have been updated successfully!")

if __name__ == "__main__":
    main() 