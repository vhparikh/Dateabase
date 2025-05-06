import os
import requests
from urllib.parse import quote

# Get the Google Maps API key from environment variable
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')

# Dictionary mapping experience types to relevant keywords for better photo matching
EXPERIENCE_TYPE_KEYWORDS = {
    'Restaurant': ['restaurant', 'dining', 'food'],
    'Bar': ['bar', 'pub', 'drinks', 'nightlife'],
    'Cafe': ['cafe', 'coffee', 'bakery'],
    'Activity': ['activity', 'attraction', 'entertainment'],
    'Outdoors': ['outdoors', 'park', 'nature', 'hiking'],
    'Other': ['point of interest', 'landmark']
}

def get_place_details(place_id, fields=None):
    """Get detailed information about a place using its place_id."""
    if not place_id:
        return None
    
    if fields is None:
        fields = ["name", "formatted_address", "geometry", "photos", "types"]
    
    fields_param = ",".join(fields)
    
    try:
        url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields={fields_param}&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('status') == 'OK' and data.get('result'):
            return data['result']
            
    except Exception as e:
        print(f"Error getting place details: {e}")
    
    return None

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
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('status') == 'OK' and data.get('candidates') and len(data['candidates']) > 0:
            place = data['candidates'][0]
            print(f"Found place: {place.get('name', 'Unknown')}")
            return place
            
    except Exception as e:
        print(f"Error finding place from text: {e}")
    
    return None

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
    
    # Prefer landscape photos if available
    if landscape_photos:
        return landscape_photos[0]
    
    # Otherwise, use any photo
    return fallback_photos[0] if fallback_photos else photos[0]

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