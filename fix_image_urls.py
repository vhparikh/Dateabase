#!/usr/bin/env python3
"""
Script to fix erroneous image URLs in the experiences table.
This script identifies Google Maps PhotoService URLs and replaces them with stable Unsplash images.
"""

import os
import sys
from flask import Flask
import re
import requests
from urllib.parse import urlparse

# Add the current directory to the path so we can import the database modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from backend.database import db, Experience
except ImportError:
    try:
        from database import db, Experience
    except ImportError:
        print("Error: Unable to import database modules. Make sure you run this script from the project root.")
        sys.exit(1)

# Create a Flask app context for database access
app = Flask(__name__)

# Get database URL from environment or use the default from the project
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://ueaqcj622ro270:pf6999e838eb1f1f2e5af5b4b9d17b2fcdc2475e46597ea2d0dcdbd6bdb1e13af@ceqbglof0h8enj.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dc26u3dpl6nepd')

# Heroku prepends "postgres://" but SQLAlchemy expects "postgresql://"
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the app with SQLAlchemy
db.init_app(app)

def is_google_maps_url(url):
    """Check if the URL is a Google Maps PhotoService URL which is likely to cause issues."""
    if not url:
        return False
    
    # Look for specific patterns in Google Maps PhotoService URLs
    patterns = [
        "PhotoService.GetPhoto",
        "maps.googleapis.com/maps/api/place/js",
        "maps.googleapis.com/maps/api/staticmap"
    ]
    
    return any(pattern in url for pattern in patterns)

def is_valid_url(url):
    """Check if a URL is valid and accessible."""
    if not url:
        return False
    
    try:
        # Parse the URL to check if it's well-formed
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            return False
        
        # Try a HEAD request to check if the URL is accessible
        response = requests.head(url, timeout=5)
        return response.status_code < 400
    except:
        return False

def get_unsplash_image_for_location(location):
    """Generate a stable Unsplash image URL for a location."""
    if not location:
        return "https://source.unsplash.com/random/800x600/?city"
    
    # Clean the location string - take just the first part before any comma
    location_clean = location.split(',')[0].strip()
    
    # Replace spaces with plus signs and remove special characters
    location_query = re.sub(r'[^a-zA-Z0-9\s]', '', location_clean).replace(' ', '+')
    
    # Return an Unsplash URL for the location
    return f"https://source.unsplash.com/random/800x600/?{location_query}"

def fix_image_urls():
    """Find and fix erroneous image URLs in the experiences table."""
    
    with app.app_context():
        print("Starting image URL fix process...")
        
        # Get all experiences
        experiences = Experience.query.all()
        print(f"Found {len(experiences)} total experiences")
        
        # Track statistics
        fixed_count = 0
        already_valid_count = 0
        empty_urls_count = 0
        
        for experience in experiences:
            # Check if the experience has an image URL
            if not experience.location_image:
                empty_urls_count += 1
                # Generate and set a new image URL
                experience.location_image = get_unsplash_image_for_location(experience.location)
                fixed_count += 1
                print(f"ID {experience.id}: Empty image URL. Set new image for '{experience.location}'")
                continue
            
            # Check if the image URL is a problematic Google Maps URL
            if is_google_maps_url(experience.location_image):
                old_url = experience.location_image
                # Generate and set a new image URL
                experience.location_image = get_unsplash_image_for_location(experience.location)
                fixed_count += 1
                print(f"ID {experience.id}: Fixed Google Maps URL for '{experience.location}'")
                print(f"  Old: {old_url[:100]}...")
                print(f"  New: {experience.location_image}")
                continue
                
            # Check if the URL is valid and accessible
            if not is_valid_url(experience.location_image):
                old_url = experience.location_image
                # Generate and set a new image URL
                experience.location_image = get_unsplash_image_for_location(experience.location)
                fixed_count += 1
                print(f"ID {experience.id}: Fixed inaccessible URL for '{experience.location}'")
                print(f"  Old: {old_url}")
                print(f"  New: {experience.location_image}")
                continue
                
            # URL is valid and accessible
            already_valid_count += 1
        
        # Commit changes to the database
        if fixed_count > 0:
            try:
                db.session.commit()
                print(f"\nSuccessfully fixed {fixed_count} image URLs")
                print(f"{already_valid_count} URLs were already valid")
                print(f"{empty_urls_count} experiences had empty image URLs and were updated")
            except Exception as e:
                db.session.rollback()
                print(f"Error committing changes to the database: {e}")
        else:
            print("No image URLs needed fixing")

if __name__ == "__main__":
    fix_image_urls() 