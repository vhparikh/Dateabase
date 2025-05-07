from flask import Blueprint, request, jsonify, current_app
from flask_cors import CORS
from functools import wraps
from datetime import datetime

# Import files
from ..utils.auth_utils import login_required
from ..database import db, User, Experience, Match, UserSwipe
from ..utils.recommender_utils import index_experience
import backend.utils.recommender_utils
from ..utils.image_utils import get_photo_url, get_place_details, find_place_from_text, select_best_photo

# Create Blueprint
experience_bp = Blueprint('experience_routes', __name__)

@experience_bp.route('/api/experiences', methods=['POST'])
@login_required()
def create_experience(current_user_id=None):
    """Create a new experience and index it in Pinecone"""
    
    # Validate and extract required fields
    data = request.json
    experience_type = data.get('experience_type', '').strip()
    experience_name = data.get('experience_name', '').strip()
    location = data.get('location', '').strip()
    description = data.get('description', '').strip()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    place_id = data.get('place_id')
    place_name = data.get('place_name')
    location_image = data.get('location_image', '')
    
    # Validate required fields
    if not experience_type:
        return jsonify({'detail': 'Experience type is required'}), 400
    if not location:
        return jsonify({'detail': 'Location is required'}), 400
    
    try:
        # Create and save the experience first
        new_experience = Experience(
            user_id=current_user_id,
            experience_type=experience_type,
            experience_name=experience_name,
            location=location,
            description=description,
            latitude=latitude,
            longitude=longitude,
            place_id=place_id,
            place_name=place_name,
            location_image=location_image
        )
        db.session.add(new_experience)
        db.session.commit()
        
        print(f"Experience created successfully with ID: {new_experience.id}")
        
        # Prepare response object
        response_data = {
            'id': new_experience.id, 
            'message': 'Experience created successfully',
            'experience': {
                'id': new_experience.id,
                'user_id': new_experience.user_id,
                'experience_type': new_experience.experience_type,
                'experience_name': new_experience.experience_name,
                'location': new_experience.location,
                'description': new_experience.description,
                'latitude': new_experience.latitude,
                'longitude': new_experience.longitude,
                'place_id': new_experience.place_id,
                'place_name': new_experience.place_name,
                'location_image': new_experience.location_image,
                'created_at': new_experience.created_at.isoformat() if new_experience.created_at else None
            }
        }
        
        # Index the experience in the recommender system
        try:
            # Only index if pinecone is enabled
            if hasattr(backend.utils.recommender_utils, 'get_pinecone_index'):
                index_success = index_experience(new_experience)
                if not index_success:
                    print(f"Warning: Failed to index experience {new_experience.id} in Pinecone")
        except Exception as e:
            print(f"Error indexing experience: {e}")
            # Don't return an error to the client - the experience was created
        
        return jsonify(response_data)
    except Exception as e:
        print(f"Error creating experience: {e}")
        db.session.rollback()
        return jsonify({'detail': str(e)}), 500

@experience_bp.route('/api/experiences', methods=['GET'])
@login_required()
def get_experiences(current_user_id=None):
    try:
        experiences = Experience.query.order_by(Experience.created_at.desc()).all()
        result = []
        
        for exp in experiences:
            creator = User.query.get(exp.user_id)
            # Clean strings to prevent any duplication
            experience_type = exp.experience_type.strip() if exp.experience_type else ''
            experience_name = exp.experience_name.strip() if exp.experience_name else ''
            location = exp.location.strip() if exp.location else ''
            description = exp.description.strip() if exp.description else ''
            
            result.append({
                'id': exp.id,
                'user_id': exp.user_id,
                'creator_name': creator.name if creator else 'Unknown',
                'experience_type': experience_type,
                'experience_name': experience_name,
                'location': location,
                'description': description,
                'latitude': exp.latitude,
                'longitude': exp.longitude,
                'place_id': exp.place_id,
                'place_name': exp.place_name,
                'location_image': exp.location_image,
                'created_at': exp.created_at.isoformat() if exp.created_at else None
            })
            
        return jsonify(result)
    except Exception as e:
        print(f"Error fetching experiences: {e}")
        return jsonify({'detail': str(e)}), 500

@experience_bp.route('/api/my-experiences', methods=['GET'])
@login_required()
def get_my_experiences(current_user_id=None):
    try:
        experiences = Experience.query.filter_by(user_id=current_user_id).order_by(Experience.created_at.desc()).all()
        result = []
        
        for exp in experiences:
            # Clean strings to prevent any duplication
            experience_type = exp.experience_type.strip() if exp.experience_type else ''
            experience_name = exp.experience_name.strip() if exp.experience_name else ''
            location = exp.location.strip() if exp.location else ''
            description = exp.description.strip() if exp.description else ''
            
            result.append({
                'id': exp.id,
                'user_id': exp.user_id,
                'experience_type': experience_type,
                'experience_name': experience_name,
                'location': location,
                'description': description,
                'latitude': exp.latitude,
                'longitude': exp.longitude,
                'place_id': exp.place_id,
                'place_name': exp.place_name,
                'location_image': exp.location_image,
                'created_at': exp.created_at.isoformat() if exp.created_at else None
            })
            
        return jsonify(result)
    except Exception as e:
        print(f"Error fetching user experiences: {e}")
        return jsonify({'detail': str(e)}), 500

@experience_bp.route('/api/experiences/get-image/<int:experience_id>', methods=['GET'])
@login_required()
def get_experience_image(experience_id, current_user_id=None):
    """Get a fresh location image for an experience using Google Places API"""
    try:
        # Fetch the experience
        experience = Experience.query.get(experience_id)
        if not experience:
            return jsonify({'detail': 'Experience not found', 'error': 'not_found'}), 404
        
        image_url = None
        
        # Try using place_id first if available
        if experience.place_id:
            place_details = get_place_details(experience.place_id)
            
            if place_details and place_details.get('photos'):
                photos = place_details.get('photos')
                best_photo = select_best_photo(photos, place_details)
                
                if best_photo:
                    image_url = get_photo_url(best_photo['photo_reference'])
        
        # If place_id doesn't work or doesn't exist, try using the location
        if not image_url and experience.location:
            place = find_place_from_text(experience.location)
            
            if place:
                if place.get('photos'):
                    best_photo = select_best_photo(place['photos'], place)
                    
                    if best_photo:
                        image_url = get_photo_url(best_photo['photo_reference'])
                        
                if not image_url and place.get('place_id'):
                    place_details = get_place_details(place['place_id'])
                    
                    if place_details and place_details.get('photos'):
                        best_photo = select_best_photo(place_details['photos'], place_details)
                        
                        if best_photo:
                            image_url = get_photo_url(best_photo['photo_reference'])
        
        # If we still don't have an image, fall back to the stored image
        if not image_url:
            image_url = experience.location_image
        
        return jsonify({'image_url': image_url})
    except Exception as e:
        print(f"Error getting experience image: {e}")
        return jsonify({'detail': str(e), 'error': 'server_error', 'image_url': None}), 500

@experience_bp.route('/api/experiences/<int:experience_id>', methods=['DELETE'])
@login_required()
def delete_experience(experience_id, current_user_id=None):
    try:
        # Fetch experience
        experience = Experience.query.get(experience_id)
        
        # Check if experience exists
        if not experience:
            return jsonify({'detail': 'Experience not found'}), 404
        
        # Check if user is authorized to delete this experience
        if experience.user_id != current_user_id:
            return jsonify({'detail': 'You are not authorized to delete this experience'}), 403
        
        # Get related matches and swipes for cleanup
        matches = Match.query.filter(
            (Match.experience_id == experience_id)
        ).all()
        
        swipes = UserSwipe.query.filter(
            (UserSwipe.experience_id == experience_id)
        ).all()
        
        # Delete related records
        for match in matches:
            db.session.delete(match)
            
        for swipe in swipes:
            db.session.delete(swipe)
        
        # Delete the experience
        db.session.delete(experience)
        db.session.commit()
        
        return jsonify({'message': 'Experience deleted successfully'}), 200
    except Exception as e:
        print(f"Error deleting experience: {e}")
        db.session.rollback()
        return jsonify({'detail': str(e)}), 500

@experience_bp.route('/api/experiences/<int:experience_id>', methods=['PUT'])
@login_required()
def update_experience(experience_id, current_user_id=None):
    try:
        # Fetch experience
        experience = Experience.query.get(experience_id)
        
        # Check if experience exists
        if not experience:
            return jsonify({'detail': 'Experience not found'}), 404
        
        # Check if user is authorized to update this experience
        if experience.user_id != current_user_id:
            return jsonify({'detail': 'You are not authorized to update this experience'}), 403
        
        # Update experience attributes
        data = request.json
        
        if 'experience_type' in data and data['experience_type'].strip():
            experience.experience_type = data['experience_type'].strip()
            
        if 'experience_name' in data:
            experience.experience_name = data['experience_name'].strip() if data['experience_name'] else None
            
        if 'location' in data and data['location'].strip():
            experience.location = data['location'].strip()
            
        if 'description' in data:
            experience.description = data['description'].strip() if data['description'] else None
            
        if 'latitude' in data:
            experience.latitude = data['latitude']
            
        if 'longitude' in data:
            experience.longitude = data['longitude']
            
        if 'place_id' in data:
            experience.place_id = data['place_id']
            
        if 'place_name' in data:
            experience.place_name = data['place_name']
            
        if 'location_image' in data:
            experience.location_image = data['location_image']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Experience updated successfully',
            'experience': {
                'id': experience.id,
                'user_id': experience.user_id,
                'experience_type': experience.experience_type,
                'experience_name': experience.experience_name,
                'location': experience.location,
                'description': experience.description,
                'latitude': experience.latitude,
                'longitude': experience.longitude,
                'place_id': experience.place_id,
                'place_name': experience.place_name,
                'location_image': experience.location_image,
                'created_at': experience.created_at.isoformat() if experience.created_at else None
            }
        }), 200
    except Exception as e:
        print(f"Error updating experience: {e}")
        db.session.rollback()
        return jsonify({'detail': str(e)}), 500

# Static route for experiences page
@experience_bp.route('/experiences')
def serve_experiences():
    return current_app.send_static_file('index.html') 