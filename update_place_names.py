#!/usr/bin/env python3
"""
Script to update existing experiences with place names from Google Places API.
This script:
1. Finds all experiences without place_name set
2. Uses either existing place_id or the location to find the place name
3. Updates the database records
"""

import os
import sys
import requests
import time
from urllib.parse import quote
from flask import Flask

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

# Get Google Maps API key from environment or use a default if available
GOOGLE_MAPS_API_KEY = os.environ.get('REACT_APP_GOOGLE_MAPS_API_KEY', 'AIzaSyCPn93Cc0sgbuZU_zhh-iup38aNSFUOKx8')

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

def get_place_details(place_id):
    """Get place details from Google Places API using place_id"""
    if not place_id:
        return None
    
    try:
        url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_address&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if data.get('status') == 'OK' and data.get('result'):
            return data['result']
    except Exception as e:
        print(f"Error getting place details: {e}")
    
    return None

def find_place_from_text(address):
    """Find place information using the address text"""
    if not address:
        return None
    
    try:
        url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={quote(address)}&inputtype=textquery&fields=name,place_id,formatted_address&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if data.get('status') == 'OK' and data.get('candidates') and len(data['candidates']) > 0:
            return data['candidates'][0]
    except Exception as e:
        print(f"Error finding place: {e}")
    
    return None

def get_place_name(experience):
    """Get place name for an experience using available data"""
    # First try using place_id if available
    if experience.place_id:
        place_details = get_place_details(experience.place_id)
        if place_details and place_details.get('name'):
            return place_details.get('name'), place_details.get('formatted_address')
    
    # If that fails, try using the location to find the place
    if experience.location:
        place_info = find_place_from_text(experience.location)
        if place_info and place_info.get('name'):
            # Also update place_id if we found it
            if place_info.get('place_id') and not experience.place_id:
                experience.place_id = place_info.get('place_id')
            return place_info.get('name'), place_info.get('formatted_address')
    
    return None, None

def update_experience_place_names():
    """Update all experiences missing place_name with data from Google Places API"""
    with app.app_context():
        print("Starting place name update process...")
        
        # Find experiences that need place name updates
        experiences = Experience.query.filter(Experience.place_name.is_(None)).all()
        print(f"Found {len(experiences)} experiences that need place name updates")
        
        update_count = 0
        for experience in experiences:
            # Add a small delay to respect API rate limits
            time.sleep(0.5)
            
            print(f"Processing experience ID {experience.id}: {experience.location}")
            place_name, formatted_address = get_place_name(experience)
            
            if place_name:
                print(f"✓ Found place name: {place_name}")
                experience.place_name = place_name
                
                # If the formatted_address is different and better than the current location,
                # we could update it too, but only if significantly different
                if formatted_address and len(formatted_address) > len(experience.location) * 1.5:
                    experience.location = formatted_address
                    print(f"  Updated location to: {formatted_address}")
                
                update_count += 1
            else:
                print(f"✗ Could not find place name for: {experience.location}")
        
        # Commit changes to the database
        if update_count > 0:
            try:
                db.session.commit()
                print(f"\nSuccessfully updated {update_count} experiences with place names")
            except Exception as e:
                db.session.rollback()
                print(f"Error committing changes to the database: {e}")
        else:
            print("No experiences needed updating")

if __name__ == "__main__":
    print("Starting place name update script...")
    update_experience_place_names() 