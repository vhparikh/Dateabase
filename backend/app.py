from flask import Flask, request, jsonify, send_from_directory, redirect, session, url_for
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
import os
import google.generativeai as genai
import json
from sqlalchemy import text

# Import auth utility functions
from .utils.auth_utils import login_required

# Import blueprints
from .routes.fix_images_route import fix_images_bp
from .routes.experience_routes import experience_bp
from .routes.swipe_routes import swipe_bp
from .routes.auth_routes import auth_bp
from .routes.match_routes import match_bp
from .routes.image_routes import image_bp

# Create the app first before registering blueprints
app = Flask(__name__, static_folder='../frontend/build', static_url_path='')
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})

# Now register the blueprint after app is defined
app.register_blueprint(fix_images_bp)
app.register_blueprint(experience_bp)
app.register_blueprint(swipe_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(match_bp)
app.register_blueprint(image_bp)

from .utils.auth_utils import validate, is_authenticated, get_cas_login_url, logout_cas, strip_ticket, _CAS_URL
from .database import db, init_db, User, Experience, Match, UserSwipe, UserImage, add_new_columns, drop_unused_columns
from .utils.recommender_utils import get_personalized_experiences, index_experience, get_embedding, get_user_preference_text, get_experience_text
import backend.utils.recommender_utils

# Setup Flask app with proper static folder configuration for production deployment
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')
# Set session type for CAS auth
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Configure Gemini API key
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Initialize the database with our app
init_db(app)

# Add phone_number and preferred_email columns if they don't exist
add_new_columns(app)

# Drop bio and dietary_restrictions columns
drop_unused_columns(app)

# Add preference vector caching columns
def add_preference_vector_columns(app):
    """Add preference_vector and preference_vector_updated_at columns to User table"""
    print("Starting migration to add preference vector caching columns...")
    with app.app_context():
        # Check if we're using SQLite or PostgreSQL
        dialect = db.engine.dialect.name
        print(f"Using {dialect} database")
        
        try:
            with db.engine.connect() as connection:
                if dialect == "sqlite":
                    # For SQLite
                    connection.execute(text('ALTER TABLE user ADD COLUMN preference_vector TEXT'))
                    connection.execute(text('ALTER TABLE user ADD COLUMN preference_vector_updated_at DATETIME'))
                    connection.commit()
                elif dialect == "postgresql":
                    # For PostgreSQL
                    connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS preference_vector TEXT'))
                    connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS preference_vector_updated_at TIMESTAMP'))
                    connection.commit()
                else:
                    print(f"Unsupported database dialect: {dialect}")
                    return False
                
                print("Preference vector caching columns added successfully!")
                return True
        except Exception as e:
            print(f"Error: {e}")
            if "duplicate column name" in str(e):
                print("Column already exists. This is fine.")
                return True
            return False

# Add preference vector caching columns
add_preference_vector_columns(app)

# User Routes
@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    new_user = User(
        username=data['username'],
        name=data['name'],
        gender=data['gender'],
        class_year=data['class_year'],
        interests=data['interests']
    )
    new_user.set_password(data['password'])
    
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'id': new_user.id, 'message': 'User created successfully'}), 201

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'name': user.name,
        'gender': user.gender,
        'class_year': user.class_year,
        'interests': user.interests,
        'profile_image': user.profile_image,
        'created_at': user.created_at
    })

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        data = request.json
        
        # Track if preference fields were updated
        preference_fields_updated = False
        
        # Update basic profile information
        if 'name' in data:
            user.name = data['name']
        if 'gender' in data:
            user.gender = data['gender']
        if 'sexuality' in data:
            user.sexuality = data['sexuality']
        if 'height' in data:
            # Validate height is within reasonable bounds
            try:
                height_val = int(data['height'])
                if height_val < 0 or height_val > 300:
                    return jsonify({'detail': 'Height must be between 0 and 300 cm'}), 400
                user.height = height_val
            except (ValueError, TypeError):
                return jsonify({'detail': 'Invalid height value. Height must be a number between 0 and 300 cm'}), 400
        if 'location' in data:
            user.location = data['location']
        if 'hometown' in data:
            user.hometown = data['hometown']
        if 'major' in data:
            user.major = data['major']
        if 'class_year' in data:
            user.class_year = data['class_year']
        if 'interests' in data:
            user.interests = data['interests']
        if 'profile_image' in data:
            user.profile_image = data['profile_image']
            
        # Handle prompts and answers
        if 'prompt1' in data:
            user.prompt1 = data['prompt1']
        if 'answer1' in data:
            user.answer1 = data['answer1']
        if 'prompt2' in data:
            user.prompt2 = data['prompt2']
        if 'answer2' in data:
            user.answer2 = data['answer2']
        if 'prompt3' in data:
            user.prompt3 = data['prompt3']
        if 'answer3' in data:
            user.answer3 = data['answer3']
        
        # Check for preference field updates
        if 'gender_pref' in data:
            user.gender_pref = data['gender_pref']
            preference_fields_updated = True
        if 'experience_type_prefs' in data:
            user.experience_type_prefs = data['experience_type_prefs']
            preference_fields_updated = True
            print(f"User {user.id}: Updated experience_type_prefs to {data['experience_type_prefs']}")
        if 'class_year_min_pref' in data:
            user.class_year_min_pref = data['class_year_min_pref']
            preference_fields_updated = True
        if 'class_year_max_pref' in data:
            user.class_year_max_pref = data['class_year_max_pref']
            preference_fields_updated = True
        if 'interests_prefs' in data:
            user.interests_prefs = data['interests_prefs']
            preference_fields_updated = True
            
        # If preferences were updated, invalidate the cached preference vector
        if preference_fields_updated:
            print(f"User {user.id}: Preferences updated, generating new preference vector")
            
            try:
                # Generate new preference text and embedding
                preference_text = get_user_preference_text(user)
                print(f"User {user.id}: Generated new preference text: {preference_text[:100]}...")
                
                if backend.utils.recommender_utils.pinecone_initialized:
                    # Get embedding for the preference text
                    preference_embedding = get_embedding(preference_text)
                    print(f"User {user.id}: Generated new preference embedding with dimension {len(preference_embedding)}")
                    
                    # Update user with new preference vector
                    user.preference_vector = json.dumps(preference_embedding)
                    user.preference_vector_updated_at = datetime.utcnow()
                    print(f"User {user.id}: Updated preference vector at {user.preference_vector_updated_at}")
                else:
                    # Reset preference vector if Pinecone is not initialized
                    user.preference_vector = None
                    user.preference_vector_updated_at = None
                    print(f"User {user.id}: Pinecone not initialized, reset preference vector")
            except Exception as e:
                print(f"User {user.id}: Error updating preference vector: {e}")
                # Reset preference vector on error
                user.preference_vector = None
                user.preference_vector_updated_at = None
            
        # Handle password updates
        if 'password' in data:
            user.set_password(data['password'])
            
        db.session.commit()
        
        # Return updated user data
        return jsonify({
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'gender': user.gender,
            'sexuality': user.sexuality,
            'height': user.height,
            'location': user.location,
            'hometown': user.hometown,
            'major': user.major,
            'class_year': user.class_year,
            'interests': user.interests,
            'profile_image': user.profile_image,
            'prompt1': user.prompt1,
            'answer1': user.answer1,
            'prompt2': user.prompt2,
            'answer2': user.answer2,
            'prompt3': user.prompt3,
            'answer3': user.answer3,
            'message': 'User updated successfully'
        })
    except Exception as e:
        print(f"Error updating user: {e}")
        db.session.rollback()
        return jsonify({'detail': str(e)}), 500

# API endpoint to get or update the current user's profile
@app.route('/api/me', methods=['GET', 'PUT'])
def get_or_update_current_user():
    """Get or update the current authenticated user's profile"""
    try:
        # Check if user is authenticated via CAS
        if not is_authenticated():
            return jsonify({'detail': 'Authentication required'}), 401
            
        user_info = session.get('user_info', {})
        netid = user_info.get('user', '')
        
        # First try to find the user by netid
        user = User.query.filter_by(netid=netid).first()
        if not user:
            # Then try by username as fallback
            user = User.query.filter_by(username=netid).first()
            
        if not user:
            return jsonify({'detail': 'User not found'}), 404
        
        # If user doesn't have netid set yet, update it
        if not user.netid:
            user.netid = netid
            db.session.commit()
        
        if request.method == 'GET':
            # Return user profile data
            return jsonify({
                'id': user.id,
                'username': user.username,
                'netid': user.netid,
                'name': user.name,
                'gender': user.gender,
                'sexuality': user.sexuality,
                'height': user.height,
                'location': user.location,
                'hometown': user.hometown,
                'major': user.major,
                'class_year': user.class_year,
                'interests': user.interests,
                'profile_image': user.profile_image,
                'prompt1': user.prompt1,
                'answer1': user.answer1,
                'prompt2': user.prompt2,
                'answer2': user.answer2,
                'prompt3': user.prompt3,
                'answer3': user.answer3,
                'onboarding_completed': user.onboarding_completed,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                # Add preference fields
                'gender_pref': user.gender_pref,
                'experience_type_prefs': user.experience_type_prefs,
                'class_year_min_pref': user.class_year_min_pref,
                'class_year_max_pref': user.class_year_max_pref,
                'interests_prefs': user.interests_prefs,
                'phone_number': user.phone_number,
                'preferred_email': user.preferred_email,
            })
        
        elif request.method == 'PUT':
            # Update user profile data
            data = request.json
            
            # Track if preference fields were updated
            preference_fields_updated = False
            
            # Only update allowed fields
            if 'name' in data:
                user.name = data['name']
            if 'gender' in data:
                user.gender = data['gender']
            if 'sexuality' in data:
                user.sexuality = data['sexuality']
            if 'height' in data:
                # Validate height is within reasonable bounds
                try:
                    height_val = int(data['height'])
                    if height_val < 0 or height_val > 300:
                        return jsonify({'detail': 'Height must be between 0 and 300 cm'}), 400
                    user.height = height_val
                except (ValueError, TypeError):
                    return jsonify({'detail': 'Invalid height value. Height must be a number between 0 and 300 cm'}), 400
            if 'location' in data:
                user.location = data['location']
            if 'hometown' in data:
                user.hometown = data['hometown']
            if 'major' in data:
                user.major = data['major']
            if 'class_year' in data:
                user.class_year = data['class_year']
            if 'interests' in data:
                user.interests = data['interests']
            if 'profile_image' in data:
                user.profile_image = data['profile_image']
            if 'prompt1' in data:
                user.prompt1 = data['prompt1']
            if 'answer1' in data:
                user.answer1 = data['answer1']
            if 'prompt2' in data:
                user.prompt2 = data['prompt2']
            if 'answer2' in data:
                user.answer2 = data['answer2']
            if 'prompt3' in data:
                user.prompt3 = data['prompt3']
            if 'answer3' in data:
                user.answer3 = data['answer3']
                
            # Handle preference fields
            if 'gender_pref' in data:
                user.gender_pref = data['gender_pref']
                preference_fields_updated = True
            if 'experience_type_prefs' in data:
                user.experience_type_prefs = data['experience_type_prefs']
                preference_fields_updated = True
                print(f"User {user.id}: Updated experience_type_prefs to {data['experience_type_prefs']}")
            if 'class_year_min_pref' in data:
                user.class_year_min_pref = data['class_year_min_pref']
                preference_fields_updated = True
            if 'class_year_max_pref' in data:
                user.class_year_max_pref = data['class_year_max_pref']
                preference_fields_updated = True
            if 'interests_prefs' in data:
                user.interests_prefs = data['interests_prefs']
                preference_fields_updated = True
                
            # If preferences were updated, invalidate the cached preference vector
            if preference_fields_updated:
                print(f"User {user.id}: Preferences updated, generating new preference vector")
                
                try:
                    # Generate new preference text and embedding
                    preference_text = get_user_preference_text(user)
                    print(f"User {user.id}: Generated new preference text: {preference_text[:100]}...")
                    
                    if backend.utils.recommender_utils.pinecone_initialized:
                        # Get embedding for the preference text
                        preference_embedding = get_embedding(preference_text)
                        print(f"User {user.id}: Generated new preference embedding with dimension {len(preference_embedding)}")
                        
                        # Update user with new preference vector
                        user.preference_vector = json.dumps(preference_embedding)
                        user.preference_vector_updated_at = datetime.utcnow()
                        print(f"User {user.id}: Updated preference vector at {user.preference_vector_updated_at}")
                    else:
                        # Reset preference vector if Pinecone is not initialized
                        user.preference_vector = None
                        user.preference_vector_updated_at = None
                        print(f"User {user.id}: Pinecone not initialized, reset preference vector")
                except Exception as e:
                    print(f"User {user.id}: Error updating preference vector: {e}")
                    # Reset preference vector on error
                    user.preference_vector = None
                    user.preference_vector_updated_at = None
                
            # Handle password updates
            if 'password' in data:
                user.set_password(data['password'])
                
            db.session.commit()
            
            # Log if preference fields were updated for visibility
            if preference_fields_updated:
                print(f"User {user.id} updated their preferences. Personalized recommendations will be refreshed.")
                
                # Pre-warm the personalized recommendations by querying Pinecone
                if backend.utils.recommender_utils.pinecone_initialized:
                    try:
                        # This won't be stored but will help with performance when the user goes to swipe
                        personalized_matches = get_personalized_experiences(user, top_k=50)
                        match_count = len(personalized_matches) if personalized_matches else 0
                        print(f"Pre-warmed {match_count} personalized matches for user {user.id}")
                    except Exception as e:
                        print(f"Error pre-warming personalized matches: {e}")
            
            # Return updated user profile
            return jsonify({
                'id': user.id,
                'username': user.username,
                'netid': user.netid,
                'name': user.name,
                'gender': user.gender,
                'sexuality': user.sexuality,
                'height': user.height,
                'location': user.location,
                'hometown': user.hometown,
                'major': user.major,
                'class_year': user.class_year,
                'interests': user.interests,
                'profile_image': user.profile_image,
                'prompt1': user.prompt1,
                'answer1': user.answer1,
                'prompt2': user.prompt2,
                'answer2': user.answer2,
                'prompt3': user.prompt3,
                'answer3': user.answer3,
                'onboarding_completed': user.onboarding_completed,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                # Add preference fields to response
                'gender_pref': user.gender_pref,
                'experience_type_prefs': user.experience_type_prefs,
                'class_year_min_pref': user.class_year_min_pref,
                'class_year_max_pref': user.class_year_max_pref,
                'interests_prefs': user.interests_prefs,
                'phone_number': user.phone_number,
                'preferred_email': user.preferred_email,
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'detail': f'Error: {str(e)}'}), 500

# Legacy endpoint - redirects to the new /api/me endpoint
@app.route('/api/users/me', methods=['GET'])
def get_current_user():
    """Legacy endpoint that redirects to the new /api/me endpoint"""
    return get_or_update_current_user()

# Endpoint to complete onboarding
@app.route('/api/users/complete-onboarding', methods=['POST'])
def complete_onboarding():
    """Mark user's onboarding as completed and update profile information"""
    try:
        print("Complete onboarding endpoint called")
        print(f"Session data: {session}")
        
        # Check if user is authenticated via CAS
        if not is_authenticated():
            print("User is not authenticated")
            return jsonify({'detail': 'Authentication required'}), 401
        
        user_info = session.get('user_info', {})
        print(f"User info from session: {user_info}")
        netid = user_info.get('user', '')
        
        if not netid:
            print("No netid found in session")
            return jsonify({'detail': 'No user identified in session'}), 401
            
        print(f"Looking up user with netid: {netid}")
        
        # First try to find the user by netid
        user = User.query.filter_by(netid=netid).first()
        if not user:
            # Then try by username as fallback
            print(f"User not found by netid, trying username")
            user = User.query.filter_by(username=netid).first()
            
        if not user:
            print(f"User not found with netid or username: {netid}")
            return jsonify({'detail': 'User not found'}), 404
            
        print(f"Found user: {user.id}, {user.username}")
        
        # Update user data from request if provided
        if request.json:
            data = request.json
            print(f"Received onboarding data: {data}")
            
            if 'name' in data and data['name']:
                user.name = data['name']
                print(f"Updated name to: {user.name}")
                
            if 'gender' in data and data['gender']:
                user.gender = data['gender']
                
            # CRITICAL: Handle sexuality explicitly - one of the fields not being saved
            if 'sexuality' in data:
                print(f"Setting sexuality to: {data['sexuality']}")
                user.sexuality = data['sexuality']
            else:
                print("No sexuality data found in request")
                
            if 'height' in data and data['height']:
                # Validate height is within reasonable bounds
                try:
                    height_val = int(data['height'])
                    if height_val < 0 or height_val > 300:
                        return jsonify({'detail': 'Height must be between 0 and 300 cm'}), 400
                    user.height = height_val
                except (ValueError, TypeError):
                    return jsonify({'detail': 'Invalid height value. Height must be a number between 0 and 300 cm'}), 400
                    
            if 'location' in data and data['location']:
                user.location = data['location']
                
            if 'hometown' in data and data['hometown']:
                user.hometown = data['hometown']
                
            if 'major' in data and data['major']:
                user.major = data['major']
                
            # CRITICAL: Handle class_year explicitly - one of the fields not being saved
            if 'class_year' in data:
                print(f"Setting class_year to: {data['class_year']}")
                user.class_year = data['class_year']
            else:
                print("No class_year data found in request")
                
            if 'interests' in data and data['interests']:
                user.interests = data['interests']
                
            if 'profile_image' in data and data['profile_image']:
                user.profile_image = data['profile_image']
                
            # CRITICAL: Handle prompts explicitly - one of the fields not being saved
            # Remove the requirement for non-empty data to still save empty values
            if 'prompt1' in data:
                print(f"Setting prompt1 to: {data['prompt1']}")
                user.prompt1 = data['prompt1']
                
            if 'answer1' in data:
                print(f"Setting answer1 to: {data['answer1']}")
                user.answer1 = data['answer1']
                
            if 'prompt2' in data:
                print(f"Setting prompt2 to: {data['prompt2']}")
                user.prompt2 = data['prompt2']
                
            if 'answer2' in data:
                print(f"Setting answer2 to: {data['answer2']}")
                user.answer2 = data['answer2']
                
            if 'prompt3' in data:
                print(f"Setting prompt3 to: {data['prompt3']}")
                user.prompt3 = data['prompt3']
                
            if 'answer3' in data:
                print(f"Setting answer3 to: {data['answer3']}")
                user.answer3 = data['answer3']
                
            if 'phone_number' in data:
                print(f"Setting phone_number to: {data['phone_number']}")
                user.phone_number = data['phone_number']
                
            if 'preferred_email' in data:
                print(f"Setting preferred_email to: {data['preferred_email']}")
                user.preferred_email = data['preferred_email']
        
        # ALWAYS mark onboarding as completed, even if no data was provided
        user.onboarding_completed = True
        db.session.commit()
        print(f"Marked onboarding as completed for user {user.id}, {user.username}")
        
        return jsonify({
            'success': True,
            'message': 'Onboarding completed successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'netid': user.netid,
                'name': user.name,
                'gender': user.gender,
                'sexuality': user.sexuality,
                'height': user.height,
                'location': user.location,
                'hometown': user.hometown,
                'major': user.major,
                'class_year': user.class_year,
                'interests': user.interests,
                'profile_image': user.profile_image,
                'prompt1': user.prompt1,
                'answer1': user.answer1,
                'prompt2': user.prompt2,
                'answer2': user.answer2,
                'prompt3': user.prompt3,
                'answer3': user.answer3,
                'onboarding_completed': user.onboarding_completed,
                'phone_number': user.phone_number,
                'preferred_email': user.preferred_email
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'detail': f'Error: {str(e)}'}), 500
    
# API endpoint to check for inappropriate content using Gemini
@app.route('/api/check-inappropriate', methods=['POST'])
def check_inappropriate():
    # Get the text content from the request
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'is_inappropriate': False, 'error': 'No text provided'}), 400
    
    try:
        # Check if Gemini API is configured
        if not GEMINI_API_KEY:
            return jsonify({'is_inappropriate': False, 'error': 'Gemini API not configured'}), 500
        
        # Use Gemini to check for inappropriate content
        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        prompt = f"Determine whether the following text is inappropriate based on general social norms, ethics, legal standards, or safety concerns. Respond only with \"true\" or \"false\".\n\nText: \"{text}\""
        
        result = model.generate_content(prompt)
        output = result.text.strip().lower()
        
        # Log the result for debugging
        print(f"Gemini check result for text: '{text[:30]}...' => {output}")
        
        # Return the result
        return jsonify({'is_inappropriate': output == 'true'})
    
    except Exception as e:
        print(f"Error checking inappropriate content: {str(e)}")
        # Fallback: if error, assume not inappropriate
        return jsonify({'is_inappropriate': False, 'error': str(e)}), 500

# Catch-all routes to handle React Router paths
@app.route('/<path:path>')
def catch_all(path):
    # First try to serve as a static file (CSS, JS, etc.)
    try:
        return app.send_static_file(path)
    except:
        # If not a static file, serve the index.html for client-side routing
        return app.send_static_file('index.html')

@app.route('/profile')
def serve_profile():
    return app.send_static_file('index.html')

@app.route('/api/users/<int:user_id>/profile', methods=['GET'])
def get_user_full_profile(user_id):
    """Get a user's full profile data including images for match details."""
    try:
        # Get the user
        user = User.query.get_or_404(user_id)
        
        # Get user's images
        user_images = UserImage.query.filter_by(user_id=user_id).order_by(UserImage.position).all()
        
        images = []
        for img in user_images:
            images.append({
                'id': img.id,
                'url': img.image_url,
                'position': img.position,
                'created_at': img.created_at.isoformat()
            })
        
        # Return complete user profile data
        return jsonify({
            'id': user.id,
            'username': user.username,
            'netid': user.netid,
            'name': user.name,
            'gender': user.gender,
            'sexuality': user.sexuality,
            'height': user.height,
            'location': user.location,
            'hometown': user.hometown,
            'major': user.major,
            'class_year': user.class_year,
            'interests': user.interests,
            'profile_image': user.profile_image,
            'prompt1': user.prompt1,
            'answer1': user.answer1,
            'prompt2': user.prompt2,
            'answer2': user.answer2,
            'prompt3': user.prompt3,
            'answer3': user.answer3,
            'images': images,
            'created_at': user.created_at.isoformat() if user.created_at else None
        })
    except Exception as e:
        print(f"Error getting user profile: {e}")
        return jsonify({'detail': str(e)}), 500

@app.route('/api/users/<int:user_id>/contact', methods=['GET'])
@login_required()
def get_user_contact_info(user_id, current_user_id=None):
    """Get a user's contact information for matches."""
    try:
        # Get the user
        user = User.query.get_or_404(user_id)
        
        # Check if users are matched (security check)
        match_exists = Match.query.filter(
            ((Match.user1_id == current_user_id) & (Match.user2_id == user_id) |
             (Match.user1_id == user_id) & (Match.user2_id == current_user_id)) &
            (Match.status == 'confirmed')
        ).first()
        
        if not match_exists:
            return jsonify({'detail': 'You can only view contact information for confirmed matches'}), 403
        
        # Return contact information
        return jsonify({
            'id': user.id,
            'name': user.name,
            'netid': user.netid,
            'class_year': user.class_year,
            'profile_image': user.profile_image,
            'phone_number': user.phone_number,
            'preferred_email': user.preferred_email
        })
    except Exception as e:
        print(f"Error getting user contact info: {e}")
        return jsonify({'detail': str(e)}), 500

# Create database tables (moved from before_first_request decorator)
def create_tables():
    with app.app_context():
        # First create all tables
        db.create_all()
        print("All database tables created successfully")

# Initialize database
with app.app_context():
    try:
        print("Creating database tables...")
        db.create_all()
        print("Tables created successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")

# Serve React frontend at root URL in production
@app.route('/')
def serve_frontend():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Removed demo data seeding
    # Use PORT environment variable for Heroku compatibility
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)