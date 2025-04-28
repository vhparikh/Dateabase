#!/usr/bin/env python3
"""
Script to update experience images in the database using Google Places API.
This script focuses on:
1. Using place_id for more reliable image fetching
2. Getting high-quality images from the Google Places API
3. Handling multiple images and prioritizing the most relevant ones
"""

import os
import sys
import requests
import time
import json
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
GOOGLE_MAPS_API_KEY = os.environ.get('REACT_APP_GOOGLE_MAPS_API_KEY', '')
if not GOOGLE_MAPS_API_KEY:
    print("Error: Google Maps API key is required. Set the REACT_APP_GOOGLE_MAPS_API_KEY environment variable.")
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

# Dictionary mapping experience types to relevant keywords for better photo matching
EXPERIENCE_TYPE_KEYWORDS = {
    'Restaurant': ['restaurant', 'dining', 'food'],
    'Bar': ['bar', 'pub', 'drinks', 'nightlife'],
    'Cafe': ['cafe', 'coffee', 'bakery'],
    'Activity': ['activity', 'attraction', 'entertainment'],
    'Outdoors': ['outdoors', 'park', 'nature', 'hiking'],
    'Other': ['point of interest', 'landmark']
}

def get_place_details(place_id):
    """
    Get detailed information about a place using its place_id.
    
    Args:
        place_id (str): The Google Place ID
        
    Returns:
        dict: Place details or None if the request failed
    """
    if not place_id:
        return None
        
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_address,photos,types&key={GOOGLE_MAPS_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('status') == 'OK' and data.get('result'):
            return data.get('result')
        else:
            print(f"Error getting place details: {data.get('status')}")
            return None
    except Exception as e:
        print(f"Exception in get_place_details: {e}")
        return None

def find_place_from_text(query):
    """
    Find a place using the Find Place API with a text query.
    
    Args:
        query (str): The search query (address or place name)
        
    Returns:
        dict: Place data or None if no place found
    """
    if not query:
        return None
        
    url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={query}&inputtype=textquery&fields=name,formatted_address,photos,place_id,types,geometry&key={GOOGLE_MAPS_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('status') == 'OK' and data.get('candidates') and len(data['candidates']) > 0:
            return data['candidates'][0]
        else:
            print(f"Error finding place from text: {data.get('status')}")
            return None
    except Exception as e:
        print(f"Exception in find_place_from_text: {e}")
        return None

def get_photo_url(photo_reference, max_width=800, max_height=600):
    """
    Get the URL for a photo using its reference ID.
    
    Args:
        photo_reference (str): The photo reference from the Places API
        max_width (int): Maximum width of the photo
        max_height (int): Maximum height of the photo
        
    Returns:
        str: Photo URL or None if the request failed
    """
    if not photo_reference:
        return None
        
    return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&maxheight={max_height}&photoreference={photo_reference}&key={GOOGLE_MAPS_API_KEY}"

def select_best_photo(photos, place_info=None):
    """
    Select the best photo from a list of photos based on relevance.
    
    Args:
        photos (list): List of photo objects from the Places API
        place_info (dict): Additional place information to help with selection
        
    Returns:
        dict: Best photo object or None if no photos available
    """
    if not photos or len(photos) == 0:
        return None
        
    # If there's only one photo, return it
    if len(photos) == 1:
        return photos[0]
        
    # Try to find the highest rated photo that is not a street view or 360 photo
    # We're using the height/width ratio as an indicator:
    # - Landscape photos (width > height) are usually better for location displays
    # - Very square photos might be logos or menu photos
    # - Very tall photos might be menus or interiors
    landscape_photos = []
    fallback_photos = []
    
    for photo in photos:
        # Skip photos without a reference
        if not photo.get('photo_reference'):
            continue
            
        # Check if photo is likely a landscape exterior shot
        if photo.get('width') and photo.get('height'):
            ratio = photo['width'] / photo['height']
            if 1.2 <= ratio <= 1.8:  # Good landscape ratio
                landscape_photos.append(photo)
            else:
                fallback_photos.append(photo)
        else:
            fallback_photos.append(photo)
    
    # Use place types to prioritize certain photos
    if place_info and place_info.get('types'):
        types = place_info.get('types', [])
        priority_photos = []
        
        # For restaurants, cafes, or bars, we want exterior shots
        if any(t in types for t in ['restaurant', 'cafe', 'bar', 'food']):
            for photo in landscape_photos:
                # Prioritize high-resolution photos
                if photo.get('width', 0) >= 1000:
                    priority_photos.append(photo)
            
            if priority_photos:
                return priority_photos[0]
    
    # Return the first landscape photo if available
    if landscape_photos:
        return landscape_photos[0]
        
    # Otherwise just return the first photo
    if fallback_photos:
        return fallback_photos[0]
    
    return photos[0]

def update_experience_image(experience):
    """
    Update a single experience with the best possible image.
    
    Args:
        experience: The experience database object
        
    Returns:
        bool: True if updated successfully, False otherwise
    """
    print(f"\nProcessing experience ID {experience.id}: {experience.location}")
    
    # Skip if no location or coordinates
    if not experience.location and (not experience.latitude or not experience.longitude):
        print("Missing location information, skipping")
        return False
    
    # Try using place_id first if available
    if experience.place_id:
        print(f"Using existing place_id: {experience.place_id}")
        place_details = get_place_details(experience.place_id)
        
        if place_details and place_details.get('photos'):
            photos = place_details.get('photos')
            best_photo = select_best_photo(photos, place_details)
            
            if best_photo:
                photo_url = get_photo_url(best_photo['photo_reference'])
                if photo_url:
                    experience.location_image = photo_url
                    print(f"✓ Updated image using existing place_id")
                    return True
    
    # If place_id doesn't work or doesn't exist, try using the location
    if experience.location:
        place = find_place_from_text(experience.location)
        
        if place:
            # Update place_id if found
            if place.get('place_id') and not experience.place_id:
                experience.place_id = place['place_id']
                
            # Update place_name if found
            if place.get('name') and not experience.place_name:
                experience.place_name = place['name']
            
            # Get photo from the place
            if place.get('photos'):
                best_photo = select_best_photo(place['photos'], place)
                
                if best_photo:
                    photo_url = get_photo_url(best_photo['photo_reference'])
                    if photo_url:
                        experience.location_image = photo_url
                        print(f"✓ Updated image using location search")
                        return True
            
            # If find_place_from_text didn't return photos but did give us a place_id,
            # try getting place details which often has more photos
            if place.get('place_id') and not place.get('photos'):
                place_details = get_place_details(place['place_id'])
                
                if place_details and place_details.get('photos'):
                    best_photo = select_best_photo(place_details['photos'], place_details)
                    
                    if best_photo:
                        photo_url = get_photo_url(best_photo['photo_reference'])
                        if photo_url:
                            experience.location_image = photo_url
                            print(f"✓ Updated image using place details")
                            return True
    
    print("⨯ Could not find a suitable image")
    return False

def update_all_experience_images():
    """
    Update all experiences in the database with high-quality images.
    """
    with app.app_context():
        print("Starting experience image update process...")
        
        # Get all experiences from the database
        experiences = Experience.query.all()
        print(f"Found {len(experiences)} total experiences")
        
        # Counters for statistics
        updated_count = 0
        skipped_count = 0
        failed_count = 0
        
        for i, experience in enumerate(experiences):
            print(f"\nProcessing {i+1}/{len(experiences)}")
            
            # Add a small delay to respect API rate limits
            time.sleep(0.5)
            
            try:
                # Update the experience image
                if update_experience_image(experience):
                    updated_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                print(f"Error updating experience {experience.id}: {e}")
                failed_count += 1
                continue
        
        # Commit all changes to the database
        try:
            db.session.commit()
            print("\nSuccessfully committed changes to the database")
        except Exception as e:
            print(f"\nError committing changes to the database: {e}")
            db.session.rollback()
            print("Changes rolled back")
        
        # Print statistics
        print("\n--- Image Update Results ---")
        print(f"Total experiences: {len(experiences)}")
        print(f"Successfully updated: {updated_count}")
        print(f"Failed to update: {failed_count}")
        print(f"Success rate: {(updated_count / len(experiences)) * 100:.1f}%")

if __name__ == "__main__":
    update_all_experience_images() 