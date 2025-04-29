from flask import Blueprint, request, jsonify, current_app
from flask_cors import CORS
from functools import wraps
from datetime import datetime

# Import login_required decorator
from .auth_utils import login_required

# Import database models
try:
    # Try local import first (for local development)
    from database import db, User, Experience, Match, UserSwipe
    from recommender import index_experience
    import recommender
except ImportError:
    # Fall back to package import (for Heroku)
    from backend.database import db, User, Experience, Match, UserSwipe
    from backend.recommender import index_experience
    import backend.recommender

# Create Blueprint
experience_bp = Blueprint('experience_routes', __name__)

@experience_bp.route('/api/experiences', methods=['POST'])
@login_required()
def create_experience(current_user_id=None):
    """Create a new experience and optionally index it in Pinecone"""
    
    # Validate and extract required fields
    data = request.json
    experience_type = data.get('experience_type', '').strip()
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
        
        # Prepare response object first
        response_data = {
            'id': new_experience.id, 
            'message': 'Experience created successfully',
            'experience': {
                'id': new_experience.id,
                'user_id': new_experience.user_id,
                'experience_type': new_experience.experience_type,
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
        
        # Try to index the experience, but don't let indexing failure affect the response
        if backend.recommender.pinecone_initialized:
            # Do the indexing in a try-except block that can't affect the main response
            try:
                print(f"Attempting to index experience {new_experience.id} in Pinecone...")
                index_result = index_experience(new_experience)
                if index_result:
                    print(f"Experience indexed in Pinecone successfully")
                    response_data['indexed'] = True
                else:
                    print(f"Warning: Failed to index experience in Pinecone, but continuing")
                    response_data['indexed'] = False
            except Exception as index_error:
                print(f"Error indexing experience in Pinecone: {index_error}")
                response_data['indexed'] = False
                # Continue even if indexing fails - don't block experience creation
        else:
            print("Pinecone not initialized. Skipping vector indexing.")
            response_data['indexed'] = False
        
        # Return success response regardless of Pinecone indexing result
        return jsonify(response_data)
        
    except Exception as db_error:
        print(f"Database error creating experience: {db_error}")
        db.session.rollback()
        return jsonify({'detail': f'Database error: {str(db_error)}'}), 500

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
            location = exp.location.strip() if exp.location else ''
            description = exp.description.strip() if exp.description else ''
            
            result.append({
                'id': exp.id,
                'user_id': exp.user_id,
                'creator_name': creator.name if creator else 'Unknown',
                'experience_type': experience_type,
                'location': location,
                'description': description,
                'latitude': exp.latitude,
                'longitude': exp.longitude,
                'place_id': exp.place_id,
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
            location = exp.location.strip() if exp.location else ''
            description = exp.description.strip() if exp.description else ''
            
            result.append({
                'id': exp.id,
                'user_id': exp.user_id,
                'experience_type': experience_type,
                'location': location,
                'description': description,
                'latitude': exp.latitude,
                'longitude': exp.longitude,
                'place_id': exp.place_id,
                'location_image': exp.location_image,
                'created_at': exp.created_at.isoformat() if exp.created_at else None
            })
            
        return jsonify(result)
    except Exception as e:
        print(f"Error fetching user experiences: {e}")
        return jsonify({'detail': str(e)}), 500

@experience_bp.route('/api/experiences/<int:experience_id>', methods=['DELETE'])
@login_required()
def delete_experience(experience_id, current_user_id=None):
    try:
        # Get the experience
        experience = db.session.get(Experience, experience_id)
        if not experience:
            return jsonify({'detail': 'Experience not found'}), 404
            
        # Check if the user owns this experience
        if experience.user_id != current_user_id:
            return jsonify({'detail': 'You can only delete your own experiences'}), 403
        
        # First, delete the experience from Pinecone if it's initialized
        if backend.recommender.pinecone_initialized and backend.recommender.pinecone_index:
            try:
                # Delete the experience from Pinecone index
                backend.recommender.pinecone_index.delete(ids=[f"exp_{experience_id}"])
                print(f"Deleted experience {experience_id} from Pinecone index")
            except Exception as e:
                print(f"Error deleting from Pinecone: {e}")
                # Continue with deletion even if Pinecone fails
        
        # Delete any matches related to this experience
        matches = Match.query.filter_by(experience_id=experience_id).all()
        for match in matches:
            print(f"Deleting match {match.id} for experience {experience_id}")
            db.session.delete(match)
        
        # Next, delete any user swipes related to this experience
        swipes = UserSwipe.query.filter_by(experience_id=experience_id).all()
        for swipe in swipes:
            print(f"Deleting user swipe {swipe.id} for experience {experience_id}")
            db.session.delete(swipe)
        
        # Now we can safely delete the experience
        print(f"Deleting experience {experience_id}")
        db.session.delete(experience)
        
        # Commit all changes
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
        # Get the experience
        experience = db.session.get(Experience, experience_id)
        if not experience:
            return jsonify({'detail': 'Experience not found'}), 404
            
        # Check if the user owns this experience
        if experience.user_id != current_user_id:
            return jsonify({'detail': 'You can only update your own experiences'}), 403
            
        # Update the experience
        data = request.json
        
        # Update fields if they exist in the request
        if 'experience_type' in data:
            experience.experience_type = data['experience_type'].strip()
        if 'location' in data:
            experience.location = data['location'].strip()
        if 'description' in data:
            experience.description = data['description'].strip()
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
        
        # Get the user (creator) to update the experience in Pinecone
        user = User.query.get(current_user_id)
        
        # Update the experience in Pinecone for vector search
        if backend.recommender.pinecone_initialized:
            index_experience(experience, user)
            print(f"Experience {experience.id} updated in Pinecone index")
        
        return jsonify({
            'message': 'Experience updated successfully',
            'experience': {
                'id': experience.id,
                'user_id': experience.user_id,
                'experience_type': experience.experience_type,
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