"""
Module to provide a Flask route for fixing erroneous image URLs in the experiences table.
This module identifies Google Maps PhotoService URLs and replaces them with stable Unsplash images.
"""

import re
import requests
from flask import Blueprint, jsonify
from urllib.parse import urlparse
from ..database import db, Experience
import time
from functools import wraps
from flask import request

# Create a blueprint for the fix images route
fix_images_bp = Blueprint('fix_images', __name__)

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
        
        # Don't do actual HTTP validation in production to avoid performance issues
        # Just check for valid URL format
        return True
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

# Simple API key check middleware for protection
def require_api_key(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        # Get API key from request header or query parameter
        api_key = request.headers.get('X-API-KEY') or request.args.get('api_key')
        
        # Check if API key is valid (uses simple string matching for illustration)
        # In production, use a more secure method like environment variables
        if api_key != "fix_images_secret_key":
            return jsonify({
                'success': False,
                'message': 'Unauthorized. Invalid API key.'
            }), 401
            
        return view_function(*args, **kwargs)
    return decorated_function

@fix_images_bp.route('/api/admin/fix-image-urls', methods=['POST'])
@require_api_key
def fix_image_urls_route():
    """Find and fix erroneous image URLs in the experiences table."""
    
    start_time = time.time()
    
    # Get optional parameter to specify fixing only problematic URLs
    fix_all = request.args.get('fix_all', 'false').lower() == 'true'
    dry_run = request.args.get('dry_run', 'false').lower() == 'true'
    experience_id = request.args.get('id')
    
    # Track statistics
    stats = {
        'total_experiences': 0,
        'fixed_count': 0,
        'already_valid_count': 0,
        'empty_urls_count': 0,
        'fixed_experiences': []
    }
    
    try:
        # Get experiences (all or a specific one)
        if experience_id:
            experiences = Experience.query.filter_by(id=experience_id).all()
        else:
            experiences = Experience.query.all()
            
        stats['total_experiences'] = len(experiences)
        
        for experience in experiences:
            # Check if the experience has an image URL
            if not experience.location_image:
                stats['empty_urls_count'] += 1
                
                if fix_all:
                    # Generate and set a new image URL
                    new_url = get_unsplash_image_for_location(experience.location)
                    
                    if not dry_run:
                        experience.location_image = new_url
                        
                    stats['fixed_count'] += 1
                    stats['fixed_experiences'].append({
                        'id': experience.id,
                        'location': experience.location,
                        'old_url': None,
                        'new_url': new_url,
                        'reason': 'empty_url'
                    })
                continue
            
            # Check if the image URL is a problematic Google Maps URL
            if is_google_maps_url(experience.location_image):
                old_url = experience.location_image
                new_url = get_unsplash_image_for_location(experience.location)
                
                if not dry_run:
                    experience.location_image = new_url
                    
                stats['fixed_count'] += 1
                stats['fixed_experiences'].append({
                    'id': experience.id,
                    'location': experience.location,
                    'old_url': old_url[:100] + '...' if len(old_url) > 100 else old_url,
                    'new_url': new_url,
                    'reason': 'google_maps_url'
                })
                continue
                
            # Check if the URL is valid
            if not is_valid_url(experience.location_image):
                old_url = experience.location_image
                new_url = get_unsplash_image_for_location(experience.location)
                
                if not dry_run:
                    experience.location_image = new_url
                    
                stats['fixed_count'] += 1
                stats['fixed_experiences'].append({
                    'id': experience.id,
                    'location': experience.location,
                    'old_url': old_url,
                    'new_url': new_url,
                    'reason': 'invalid_url'
                })
                continue
                
            # URL is valid
            stats['already_valid_count'] += 1
        
        # Commit changes to the database if not a dry run
        if stats['fixed_count'] > 0 and not dry_run:
            db.session.commit()
            
        execution_time = time.time() - start_time
            
        return jsonify({
            'success': True,
            'dry_run': dry_run,
            'fix_all': fix_all,
            'execution_time_seconds': round(execution_time, 2),
            'stats': {
                'total_experiences': stats['total_experiences'],
                'fixed_count': stats['fixed_count'],
                'already_valid_count': stats['already_valid_count'],
                'empty_urls_count': stats['empty_urls_count'],
            },
            'fixed_experiences': stats['fixed_experiences'][:20],  # Limit to 20 to avoid huge responses
            'total_fixed_experiences': len(stats['fixed_experiences'])
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f"Error fixing image URLs: {str(e)}"
        }), 500 