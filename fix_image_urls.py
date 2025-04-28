#!/usr/bin/env python3
"""
Script to update experience images in the database with high-quality photos 
from Google Places API using a more efficient approach.

This script:
1. Prioritizes using the address directly with Find Place API
2. Fetches multiple photos and selects the most relevant one
3. Handles fallbacks gracefully
"""

import os
import sys
import re
import requests
import time
import json
import random
from urllib.parse import urlparse, quote
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

# Keywords to prioritize and deprecate in photo selection
PREFERRED_KEYWORDS = [
    'exterior', 'outside', 'building', 'street', 'facade', 'front', 'storefront',
    'entrance', 'sign', 'logo', 'landmark', 'attraction', 'scenery', 'view'
]

AVOID_KEYWORDS = [
    'hotel', 'room', 'suite', 'bed', 'bedroom', 'interior', 'apartment', 'living', 
    'lobby', 'bathroom', 'kitchen', 'dining', 'food', 'meal', 'dish', 'drink',
    'menu', 'receipt', 'selfie', 'person', 'people', 'crowd'
]

# Match experience types to photo search terms for better relevance
EXPERIENCE_TYPE_KEYWORDS = {
    'Restaurant': ['restaurant', 'dining', 'eatery'],
    'Cafe': ['cafe', 'coffee shop', 'bakery'],
    'Bar': ['bar', 'pub', 'cocktail'],
    'Park': ['park', 'garden', 'outdoor'],
    'Museum': ['museum', 'gallery', 'exhibit'],
    'Theater': ['theater', 'cinema', 'stage'],
    'Concert': ['concert hall', 'music venue', 'arena'],
    'Hiking': ['trail', 'mountain', 'forest'],
    'Beach': ['beach', 'coast', 'ocean'],
    'Shopping': ['mall', 'store', 'shop'],
    'Sports': ['stadium', 'arena', 'field'],
    'Festival': ['festival grounds', 'event space'],
    'Class': ['school', 'university', 'studio'],
    'Club': ['nightclub', 'disco'],
}

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

def is_static_map_url(url):
    """Check if the URL is a Google Static Maps URL."""
    if not url:
        return False
    
    return "maps.googleapis.com/maps/api/staticmap" in url

def is_places_photo_url(url):
    """Check if the URL is a Google Places Photo API URL."""
    if not url:
        return False
    
    return "maps.googleapis.com/maps/api/place/photo" in url

def find_place_from_text(address, fields=None):
    """
    Get place data directly from an address string using Find Place API.
    This is the most efficient way to get place data including photos.
    """
    if not address:
        return None
    
    if fields is None:
        fields = ["place_id", "name", "formatted_address", "geometry", "photos", "types"]
    
    fields_param = ",".join(fields)
    
    try:
        url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={quote(address)}&inputtype=textquery&fields={fields_param}&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if data.get('status') == 'OK' and data.get('candidates') and len(data['candidates']) > 0:
            place = data['candidates'][0]
            print(f"Found place: {place.get('name', 'Unknown')}")
            return place
            
    except Exception as e:
        print(f"Error finding place from text: {e}")
    
    return None

def get_place_details(place_id, fields=None):
    """Get detailed information about a place using its place_id."""
    if not place_id:
        return None
    
    if fields is None:
        fields = ["name", "formatted_address", "geometry", "photos", "types", "url"]
    
    fields_param = ",".join(fields)
    
    try:
        url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields={fields_param}&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if data.get('status') == 'OK' and data.get('result'):
            return data['result']
            
    except Exception as e:
        print(f"Error getting place details: {e}")
    
    return None

def find_places_nearby(lat, lng, radius=200, type=None, keyword=None):
    """Find places near a location for alternative image sources."""
    if lat is None or lng is None:
        return []
    
    try:
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&key={GOOGLE_MAPS_API_KEY}"
        
        if type:
            url += f"&type={type}"
        
        if keyword:
            url += f"&keyword={quote(keyword)}"
        
        response = requests.get(url)
        data = response.json()
        
        if data.get('status') == 'OK' and data.get('results'):
            # Prioritize places with photos
            places_with_photos = [place for place in data['results'] if place.get('photos')]
            if places_with_photos:
                return places_with_photos
            
            return data['results']
            
    except Exception as e:
        print(f"Error finding nearby places: {e}")
    
    return []

def text_search_places(query):
    """Find places by text search."""
    if not query:
        return []
    
    try:
        url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={quote(query)}&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if data.get('status') == 'OK' and data.get('results'):
            return data['results']
            
    except Exception as e:
        print(f"Error searching for places by text: {e}")
    
    return []

def score_photo(photo, place_data):
    """
    Rate how good a photo is for representing a location,
    based on various quality factors and relevance.
    """
    if not photo:
        return 0
    
    score = 0
    
    # Size score - prefer larger photos
    width = photo.get('width', 0)
    height = photo.get('height', 0)
    
    # Prefer landscape orientation for display
    if width > height:
        score += 3
    
    # Prefer higher resolution images
    size_score = min((width * height) / 100000, 10)
    score += size_score
    
    # Analyze photo attribution for keywords
    if photo.get('html_attributions'):
        attr_text = ' '.join(photo.get('html_attributions', [])).lower()
        
        # Preferred keywords
        for keyword in PREFERRED_KEYWORDS:
            if keyword in attr_text:
                score += 5
                break
        
        # Keywords to avoid
        for keyword in AVOID_KEYWORDS:
            if keyword in attr_text:
                score -= 8
                break
    
    # Relevant to experience type
    place_types = place_data.get('types', [])
    if 'restaurant' in place_types and 'food' in place_types:
        if 'exterior' in attr_text or 'outside' in attr_text or 'building' in attr_text:
            score += 5
    
    return score

def select_best_photo(photos, place_data):
    """Select the most appropriate photo from a list based on relevance."""
    if not photos or len(photos) == 0:
        return None
    
    # If only one photo, return it
    if len(photos) == 1:
        return photos[0]
    
    # Score each photo
    scored_photos = [(photo, score_photo(photo, place_data)) for photo in photos]
    
    # Sort by score, highest first
    scored_photos.sort(key=lambda x: x[1], reverse=True)
    
    # Print info about top photos for debugging
    for i, (photo, score) in enumerate(scored_photos[:min(3, len(scored_photos))]):
        attr = photo.get('html_attributions', ['No attribution'])
        print(f"Photo #{i+1} score: {score:.1f}, Width: {photo.get('width', 'unknown')}x{photo.get('height', 'unknown')}")
    
    # Return the highest scoring photo
    return scored_photos[0][0] if scored_photos else None

def get_photo_url(photo_reference, max_width=800):
    """Convert a photo reference to a Google Places Photo API URL."""
    if not photo_reference:
        return None
    
    return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&photoreference={photo_reference}&key={GOOGLE_MAPS_API_KEY}"

def get_street_view_url(location=None, lat=None, lng=None, size="600x400"):
    """Get a Street View image URL based on location or coordinates."""
    if lat is not None and lng is not None:
        return f"https://maps.googleapis.com/maps/api/streetview?size={size}&location={lat},{lng}&key={GOOGLE_MAPS_API_KEY}"
    elif location:
        return f"https://maps.googleapis.com/maps/api/streetview?size={size}&location={quote(location)}&key={GOOGLE_MAPS_API_KEY}"
    return None

def get_static_map_url(location=None, lat=None, lng=None, zoom=16, size="600x400"):
    """Get a static map image URL as a last resort."""
    if lat is not None and lng is not None:
        return f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom={zoom}&size={size}&maptype=roadmap&markers=color:red%7C{lat},{lng}&key={GOOGLE_MAPS_API_KEY}"
    elif location:
        return f"https://maps.googleapis.com/maps/api/staticmap?center={quote(location)}&zoom={zoom}&size={size}&maptype=roadmap&markers=color:red%7C{quote(location)}&key={GOOGLE_MAPS_API_KEY}"
    return None

def get_best_image_for_experience(experience):
    """
    Get the best possible image for an experience using the most efficient approach.
    """
    print(f"\nProcessing experience ID {experience.id}: {experience.location}")
    
    location = experience.location
    experience_type = experience.experience_type
    lat = experience.latitude
    lng = experience.longitude
    place_id = experience.place_id
    
    # Create a context for the photo search based on experience type
    search_context = EXPERIENCE_TYPE_KEYWORDS.get(experience_type, [experience_type]) if experience_type else []
    
    # APPROACH 1: Use the place_id if it already exists
    if place_id:
        print(f"Using existing place_id: {place_id}")
        place_details = get_place_details(place_id)
        
        if place_details and place_details.get('photos'):
            photos = place_details.get('photos')
            best_photo = select_best_photo(photos, place_details)
            
            if best_photo:
                photo_url = get_photo_url(best_photo['photo_reference'])
                print(f"✓ Found photo using existing place_id")
                return photo_url
    
    # APPROACH 2: Direct place lookup from address
    if location:
        print(f"Finding place from address: {location}")
        place = find_place_from_text(location)
        
        if place:
            if place.get('place_id'):
                # Update the place_id in our database for future uses
                experience.place_id = place['place_id']
            
            if place.get('photos'):
                best_photo = select_best_photo(place['photos'], place)
                
                if best_photo:
                    photo_url = get_photo_url(best_photo['photo_reference'])
                    print(f"✓ Found photo directly from address")
                    return photo_url
                
            # If findplacefromtext didn't return photos but did give us a place_id,
            # try getting details which often contains more photos
            if place.get('place_id') and not place.get('photos'):
                place_details = get_place_details(place['place_id'])
                
                if place_details and place_details.get('photos'):
                    best_photo = select_best_photo(place_details['photos'], place_details)
                    
                    if best_photo:
                        photo_url = get_photo_url(best_photo['photo_reference'])
                        print(f"✓ Found photo from place details")
                        return photo_url
    
    # APPROACH 3: Try searching with location + context keywords
    if location and search_context:
        for keyword in search_context:
            search_query = f"{location} {keyword}"
            print(f"Searching for: {search_query}")
            
            search_results = text_search_places(search_query)
            for place in search_results[:2]:  # Only check top 2 results
                if place.get('photos'):
                    best_photo = select_best_photo(place['photos'], place)
                    
                    if best_photo:
                        photo_url = get_photo_url(best_photo['photo_reference'])
                        print(f"✓ Found photo from text search with context")
                        return photo_url
    
    # APPROACH 4: Try nearby places if we have coordinates
    if lat is not None and lng is not None:
        # Look for nearby places with specific types
        place_types = ['tourist_attraction', 'point_of_interest']
        
        # Add type based on experience type if relevant
        if experience_type and experience_type.lower() in ['restaurant', 'cafe', 'bar']:
            place_types.insert(0, experience_type.lower())
        
        for place_type in place_types:
            nearby_places = find_places_nearby(lat, lng, radius=200, type=place_type)
            
            for place in nearby_places[:3]:  # Check top 3 nearby places
                if place.get('photos'):
                    best_photo = select_best_photo(place['photos'], place)
                    
                    if best_photo:
                        photo_url = get_photo_url(best_photo['photo_reference'])
                        print(f"✓ Found photo from nearby {place_type}")
                        return photo_url
    
    # APPROACH 5: Try Street View as a fallback for establishments
    if lat is not None and lng is not None:
        print("Trying Street View image")
        street_view_url = get_street_view_url(lat=lat, lng=lng)
        
        # We don't have a reliable way to check if Street View has an image beforehand
        # So we'll just return the URL and let the client handle fallbacks
        print("⚠ Falling back to Street View image")
        return street_view_url
    
    # FINAL FALLBACK: Static Map
    print("⚠ Falling back to static map image")
    return get_static_map_url(location, lat, lng)

def update_all_experience_images():
    """Update all experiences with better images."""
    
    with app.app_context():
        print("Starting experience image update process...")
        
        # Get all experiences from the database
        experiences = Experience.query.all()
        print(f"Found {len(experiences)} total experiences")
        
        # Counters for statistics
        updated_count = 0
        skipped_count = 0
        failed_count = 0
        
        for experience in experiences:
            # Add a small delay to respect API rate limits
            time.sleep(0.5)
            
            # Skip experiences with already good images
            current_image_url = experience.location_image
            if current_image_url and not is_static_map_url(current_image_url) and not is_places_photo_url(current_image_url):
                # If it's a valid URL and not from Google Maps APIs, keep it
                if is_valid_url(current_image_url):
                    print(f"ID {experience.id}: Already has a good image, skipping")
                    skipped_count += 1
                    continue
            
            # Get the best image for this experience
            new_image_url = get_best_image_for_experience(experience)
            
            # Skip if we couldn't generate a valid URL
            if not new_image_url:
                print(f"ID {experience.id}: Failed to find a good image")
                failed_count += 1
                continue
            
            # Don't replace a good photo with a static map
            if not is_static_map_url(current_image_url) and is_static_map_url(new_image_url):
                print(f"ID {experience.id}: Keeping existing photo (better than static map)")
                skipped_count += 1
                continue
            
            # Update the image URL
            old_url = experience.location_image
            experience.location_image = new_image_url
            updated_count += 1
            
            print(f"ID {experience.id}: Updated image for '{experience.location}'")
            if old_url:
                print(f"  Old: {old_url[:80] + '...' if len(old_url) > 80 else old_url}")
            print(f"  New: {new_image_url[:80] + '...' if len(new_image_url) > 80 else new_image_url}")
        
        # Commit changes to the database
        if updated_count > 0:
            try:
                db.session.commit()
                print(f"\nSummary:")
                print(f"✓ Successfully updated {updated_count} experience images")
                print(f"- Skipped {skipped_count} experiences with already good images")
                print(f"✗ Failed to find good images for {failed_count} experiences")
            except Exception as e:
                db.session.rollback()
                print(f"Error committing changes to the database: {e}")
        else:
            print("No experience images needed updating")

if __name__ == "__main__":
    print("Starting experience image update script...")
    print("This will scan all experiences and update them with high-quality images.")
    update_all_experience_images() 