from flask import Flask, request, jsonify, send_from_directory, redirect, session, url_for
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
import os
import jwt
import secrets
from urllib.parse import quote_plus, urlencode, quote
try:
    # Try local import first (for local development)
    from auth import validate, is_authenticated, get_cas_login_url, logout_cas, strip_ticket, _CAS_URL
    from database import db, init_db, User, Experience, Match, UserSwipe
except ImportError:
    # Fall back to package import (for Heroku)
    from backend.auth import validate, is_authenticated, get_cas_login_url, logout_cas, strip_ticket, _CAS_URL
    from backend.database import db, init_db, User, Experience, Match, UserSwipe
from functools import wraps

# Setup Flask app with proper static folder configuration for production deployment
app = Flask(__name__, 
           static_folder='../frontend/build',  # Path to the React build directory
           static_url_path='')  # Empty string makes the static assets available at the root URL
CORS(app, supports_credentials=True)

# Set up app configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')
# Set session type for CAS auth
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Initialize the database with our app
init_db(app)

# Auth Helper Functions
def generate_token(user_id):
    payload = {
        'exp': datetime.utcnow() + timedelta(days=1),
        'iat': datetime.utcnow(),
        'sub': user_id
    }
    return jwt.encode(
        payload,
        app.config['SECRET_KEY'],
        algorithm='HS256'
    )

def decode_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return 'Signature expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'

# Authentication decorator for protected routes
def login_required():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            print(f"Authenticating request to {f.__name__}")
            
            # Check if user is authenticated via session
            if not session.get('user_info'):
                print(f"No user_info found in session for {f.__name__}")
                return jsonify({'detail': 'Authentication required'}), 401
            
            # Get user info from session
            user_info = session.get('user_info')
            netid = user_info.get('user', '')
            print(f"Found session for user {netid}")
            
            # Get the user from database
            user = User.query.filter_by(netid=netid).first()
            if not user:
                print(f"User with netid {netid} not found in database")
                return jsonify({'detail': 'User not found'}), 401
            
            print(f"Authenticated user: {user.username}, ID: {user.id}")
            
            # Add user_id to kwargs so it's available in the view function
            kwargs['current_user_id'] = user.id
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Get current user ID from session
def get_current_user_id():
    if not session.get('user_info'):
        return None
    
    user_info = session.get('user_info')
    netid = user_info.get('user', '')
    
    user = User.query.filter_by(netid=netid).first()
    if not user:
        return None
    
    return user.id

# Auth Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    
    # Check if username already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'detail': 'Username already exists'}), 400
    
    # Create new user
    new_user = User(
        username=data['username'],
        name=data['name'],
        gender=data['gender'],
        class_year=data['class_year'],
        interests=data['interests'],
        profile_image=data.get('profile_image')
    )
    new_user.set_password(data['password'])
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/token', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'detail': 'Please provide both username and password'}), 400
    
    try:
        # Find the user with the given username
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({'detail': 'Invalid username or password'}), 401
            
        access_token = jwt.encode({
            'sub': user.id,
            'username': user.username,
            'exp': datetime.now(timezone.utc) + timedelta(days=30)  # Extended token validity
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        refresh_token = jwt.encode({
            'sub': user.id,
            'exp': datetime.now(timezone.utc) + timedelta(days=90)  # Extended refresh token
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'access': access_token,
            'refresh': refresh_token
        })
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'detail': str(e)}), 500

@app.route('/api/token/refresh', methods=['POST'])
def refresh_token():
    refresh = request.json.get('refresh')
    
    try:
        # If no refresh token provided, check if user is authenticated via CAS session
        if not refresh:
            # Check if user is authenticated via CAS
            if not is_authenticated():
                return jsonify({'detail': 'Authentication required'}), 401
            
            user_info = session.get('user_info', {})
            netid = user_info.get('user', '')
            
            # Find the user by netid
            user = User.query.filter_by(netid=netid).first()
            if not user:
                return jsonify({'detail': 'User not found'}), 404
            
            # Generate new tokens
            access_token = jwt.encode({
                'sub': user.id,
                'username': user.username,
                'exp': datetime.now(timezone.utc) + timedelta(days=30)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            
            refresh_token = jwt.encode({
                'sub': user.id,
                'exp': datetime.now(timezone.utc) + timedelta(days=90)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            
            return jsonify({
                'access': access_token,
                'refresh': refresh_token
            })
        else:
            # Handle provided refresh token
            user_id = decode_token(refresh)
            if isinstance(user_id, str) and user_id.startswith('Invalid'):
                return jsonify({'detail': user_id}), 401
                
            user = User.query.get(user_id)
            if not user:
                return jsonify({'detail': 'User not found'}), 404
            
            access_token = jwt.encode({
                'sub': user.id,
                'username': user.username,
                'exp': datetime.now(timezone.utc) + timedelta(days=30)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            
            return jsonify({
                'access': access_token,
                'refresh': refresh  # Return the same refresh token
            })
    except Exception as e:
        print(f"Error in refresh_token: {e}")
        return jsonify({'detail': str(e)}), 500

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

@app.route('/api/experiences', methods=['POST'])
@login_required()
def create_experience(current_user_id=None):
    try:
        print(f"Creating experience for user ID: {current_user_id}")
        
        # Check if we received JSON data
        if not request.is_json:
            print("Error: Request does not contain JSON data")
            return jsonify({'detail': 'Request must be JSON'}), 400
            
        data = request.json
        print(f"Received data: {data}")
        
        if not data:
            return jsonify({'detail': 'No data provided'}), 400
        
        required_fields = ['experience_type', 'location']
        for field in required_fields:
            if field not in data:
                print(f"Missing required field: {field}")
                return jsonify({'detail': f'Missing required field: {field}'}), 400
                
        # Use authenticated user's ID instead of passing it in the request
        user = User.query.get(current_user_id)
        if not user:
            print(f"User not found with ID: {current_user_id}")
            return jsonify({'detail': 'User not found'}), 404
        
        print(f"Creating experience for user: {user.username}")
        
        # Clean up input data to prevent duplication
        experience_type = data['experience_type'].strip() if data['experience_type'] else ''
        location = data['location'].strip() if data['location'] else ''
        description = data.get('description', '').strip()
        
        # Handle new fields
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        place_id = data.get('place_id', '').strip() if data.get('place_id') else None
        location_image = data.get('location_image', '').strip() if data.get('location_image') else None
        
        tags = data.get('tags', [])
        
        print(f"Creating experience with type: {experience_type}, location: {location}")
        
        new_experience = Experience(
            user_id=current_user_id,
            experience_type=experience_type,
            location=location,
            description=description,
            latitude=latitude,
            longitude=longitude,
            place_id=place_id,
            location_image=location_image
        )
        db.session.add(new_experience)
        db.session.commit()
        
        print(f"Experience created successfully with ID: {new_experience.id}")
        
        return jsonify({
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
                'location_image': new_experience.location_image,
                'created_at': new_experience.created_at.isoformat() if new_experience.created_at else None
            }
        }), 201
    except Exception as e:
        print(f"Error creating experience: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'detail': str(e)}), 500

@app.route('/api/experiences', methods=['GET'])
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

@app.route('/api/my-experiences', methods=['GET'])
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

@app.route('/api/experiences/<int:experience_id>', methods=['DELETE'])
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
        
        # First, delete any matches related to this experience
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

@app.route('/api/experiences/<int:experience_id>', methods=['PUT'])
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
        if 'location_image' in data:
            experience.location_image = data['location_image']
            
        db.session.commit()
        
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
                'location_image': experience.location_image,
                'created_at': experience.created_at.isoformat() if experience.created_at else None
            }
        }), 200
    except Exception as e:
        print(f"Error updating experience: {e}")
        db.session.rollback()
        return jsonify({'detail': str(e)}), 500

@app.route('/api/swipes', methods=['POST'])
@login_required()
def record_swipe(current_user_id=None):
    try:
        data = request.json
        
        # Validate required fields
        if not all(key in data for key in ['experience_id', 'is_like']):
            return jsonify({'detail': 'Missing required fields'}), 400
            
        # Get the experience
        experience = db.session.get(Experience, data['experience_id'])
        if not experience:
            return jsonify({'detail': 'Experience not found'}), 404
            
        # Check if the user owns this experience
        if experience.user_id == current_user_id:
            return jsonify({'detail': 'Cannot swipe on your own experience'}), 400
            
        # Create or update the swipe
        swipe = UserSwipe.query.filter_by(
            user_id=current_user_id,
            experience_id=data['experience_id']
        ).first()
        
        if not swipe:
            swipe = UserSwipe(
                user_id=current_user_id,
                experience_id=data['experience_id'],
                direction=data['is_like']
            )
            db.session.add(swipe)
        else:
            swipe.direction = data['is_like']
            
        db.session.commit()
        
        # Check for match
        match = False
        if data['is_like']:  # Only create match if user swiped yes
            # Check if the experience creator has also liked this user's experiences
            # Get experiences created by the current user
            user_experiences = Experience.query.filter_by(user_id=current_user_id).all()
            experience_creator = experience.user_id
            
            # Check for mutual interest
            for user_exp in user_experiences:
                matching_swipe = UserSwipe.query.filter_by(
                    user_id=experience_creator,
                    experience_id=user_exp.id,
                    direction=True
                ).first()
                
                if matching_swipe:
                    match = True
                    
                    # Check if match already exists
                    existing_match = Match.query.filter(
                        ((Match.user1_id == current_user_id) & (Match.user2_id == experience_creator)) |
                        ((Match.user1_id == experience_creator) & (Match.user2_id == current_user_id))
                    ).first()
                    
                    if not existing_match:
                        # Create a match record between the two users
                        match_record = Match(
                            user1_id=current_user_id,
                            user2_id=experience_creator,
                            experience_id=data['experience_id'],
                            status='pending'  # Pending until both users confirm
                        )
                        db.session.add(match_record)
                        db.session.commit()
                    break  # Only create one match between users
            
            # Also create a potential match for the experience owner to review
            potential_match = Match.query.filter(
                (Match.user1_id == current_user_id) & 
                (Match.user2_id == experience_creator) &
                (Match.experience_id == data['experience_id'])
            ).first()
            
            if not potential_match and not match:
                potential_match = Match(
                    user1_id=current_user_id,
                    user2_id=experience_creator,
                    experience_id=data['experience_id'],
                    status='pending'
                )
                db.session.add(potential_match)
                db.session.commit()
        
        return jsonify({
            'message': 'Swipe recorded successfully',
            'match': match
        }), 200
    except Exception as e:
        print(f"Error recording swipe: {e}")
        db.session.rollback()
        return jsonify({'detail': str(e)}), 500

@app.route('/api/matches/<int:user_id>', methods=['GET'])
def get_matches(user_id):
    try:
        # Get both confirmed and pending matches for this user
        all_matches = Match.query.filter(
            (Match.user1_id == user_id) | (Match.user2_id == user_id)
        ).all()
        
        confirmed_matches = []
        pending_received = []  # Matches where user is the experience owner and needs to accept
        pending_sent = []      # Matches where user liked someone else's experience
        
        for match in all_matches:
            # Determine the other user in the match
            other_user_id = match.user2_id if match.user1_id == user_id else match.user1_id
            other_user = User.query.get(other_user_id)
            experience = Experience.query.get(match.experience_id)
            
            if not other_user or not experience:
                continue
            
            match_data = {
                'match_id': match.id,
                'other_user': {
                    'id': other_user.id,
                    'name': other_user.name,
                    'gender': other_user.gender,
                    'class_year': other_user.class_year,
                    'profile_image': other_user.profile_image if hasattr(other_user, 'profile_image') else None
                },
                'experience': {
                    'id': experience.id,
                    'experience_type': experience.experience_type,
                    'location': experience.location,
                    'description': experience.description,
                    'latitude': experience.latitude,
                    'longitude': experience.longitude,
                    'place_id': experience.place_id,
                    'location_image': experience.location_image,
                    'owner_id': experience.user_id
                },
                'created_at': match.created_at.isoformat() if match.created_at else None,
                'status': match.status
            }
            
            # Categorize the match
            if match.status == 'confirmed':
                confirmed_matches.append(match_data)
            elif match.status == 'pending':
                # If user is the experience owner, they need to accept/reject
                if experience.user_id == user_id:
                    pending_received.append(match_data)
                else:
                    # User sent the like
                    pending_sent.append(match_data)
        
        # Return categorized matches
        return jsonify({
            'confirmed': confirmed_matches,
            'pending_received': pending_received,
            'pending_sent': pending_sent
        })
    except Exception as e:
        print(f"Error fetching matches: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommendations/<int:user_id>', methods=['GET'])
def get_recommendations(user_id):
    try:
        # This is a simple recommendation system
        # In reality, you would use more sophisticated algorithms
        
        # Get all experiences except those created by the user
        experiences = Experience.query.filter(Experience.user_id != user_id).all()
        
        # Get all experiences that the user has already swiped on
        swiped_experience_ids = [swipe.experience_id for swipe in UserSwipe.query.filter_by(user_id=user_id).all()]
        
        # Filter out experiences that the user has already swiped on
        available_experiences = [exp for exp in experiences if exp.id not in swiped_experience_ids]
        
        # Sort by most recent first
        available_experiences.sort(key=lambda x: x.created_at, reverse=True)
        
        # If no experiences are available, simply return an empty list
        if not available_experiences:
            # Don't reset user swipes as we want to respect user preferences
            # Just return empty result to indicate no more experiences to show
            return jsonify([])
            
        result = []
        for exp in available_experiences:
            creator = User.query.get(exp.user_id)
            # Clean strings to prevent any duplication
            experience_type = exp.experience_type.strip() if exp.experience_type else ''
            location = exp.location.strip() if exp.location else ''
            description = exp.description.strip() if exp.description else ''
            
            creator_data = {
                'id': creator.id,
                'username': creator.username,
                'name': creator.name
            }
            
            # Add profile image if exists
            if hasattr(creator, 'profile_image') and creator.profile_image:
                creator_data['profile_image'] = creator.profile_image
            
            result.append({
                'id': exp.id,
                'user_id': exp.user_id,
                'creator': creator_data,
                'experience_type': experience_type,
                'location': location,
                'description': description,
                'latitude': exp.latitude,
                'longitude': exp.longitude,
                'place_id': exp.place_id,
                'location_image': exp.location_image,
                'created_at': exp.created_at.isoformat() if exp.created_at else None
            })
        
        # No longer create dummy experiences - only show real user-created experiences
        # If there are no experiences available, just return the empty list
        
        return jsonify(result)
    except Exception as e:
        print(f"Error fetching recommendations: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/swipe-experiences', methods=['GET'])
@login_required()
def get_swipe_experiences(current_user_id=None):
    try:
        # Get experiences that are not created by the current user
        experiences = Experience.query.filter(Experience.user_id != current_user_id).order_by(Experience.created_at.desc()).all()
        
        result = []
        for exp in experiences:
            # Get the creator of the experience
            creator = User.query.get(exp.user_id)
            
            # Clean strings to prevent any duplication
            experience_type = exp.experience_type.strip() if exp.experience_type else ''
            location = exp.location.strip() if exp.location else ''
            description = exp.description.strip() if exp.description else ''
            
            result.append({
                'id': exp.id,
                'user_id': exp.user_id,
                'creator_name': creator.name if creator else 'Unknown',
                'creator_netid': creator.netid if creator else '',
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
        print(f"Error fetching swipe experiences: {e}")
        return jsonify({'detail': str(e)}), 500

# CAS Authentication routes
@app.route('/api/cas/login', methods=['GET'])
def cas_login():
    """Initiate CAS login process and return login URL"""
    try:
        callback_url = request.args.get('callback_url', '/')
        login_url = get_cas_login_url(callback_url)
        return jsonify({'login_url': login_url})
    except Exception as e:
        return jsonify({'detail': f'Error: {str(e)}'}), 500

@app.route('/api/cas/callback', methods=['GET'])
def cas_callback():
    """Process CAS authentication callback"""
    try:
        ticket = request.args.get('ticket')
        callback_url = request.args.get('callback_url', '/')
        
        # Determine the frontend URL based on environment
        # In production, the app is served from the same domain
        if 'herokuapp.com' in request.host or os.environ.get('PRODUCTION') == 'true':
            # In production, use the same host
            scheme = request.headers.get('X-Forwarded-Proto', 'https')
            frontend_url = f"{scheme}://{request.host}"
        else:
            # In development, get from Origin header or use localhost:3000 as fallback
            frontend_url = request.headers.get('Origin', 'http://localhost:3000')
        
        if not ticket:
            return jsonify({'detail': 'No ticket provided'}), 400
        
        # Validate ticket with CAS server
        user_info = validate(ticket)
        
        if not user_info:
            return jsonify({'detail': 'Invalid CAS ticket'}), 401
        
        # Store user info in session
        session['user_info'] = user_info
        netid = user_info.get('user', '')
        
        # Extract attributes for more user information if available
        attributes = user_info.get('attributes', {})
        # Use principalId as the cas_id if available, otherwise use netid
        cas_id = attributes.get('principalId', netid)
        
        # Check if user exists in our database - first by netid, then by cas_id
        user = User.query.filter_by(netid=netid).first()
        if not user:
            user = User.query.filter_by(cas_id=cas_id).first()
        
        # If user doesn't exist, we'll create one with information from CAS
        if not user:
            # Get display name or default to netID
            display_name = attributes.get('displayName', f"{netid.capitalize()} User")
            
            # Create a new user with the netid and cas_id
            new_user = User(
                username=netid,
                netid=netid,
                cas_id=cas_id,
                name=display_name,
                # Set optional fields to default values that can be updated later
                gender='Other',
                class_year=2025,
                interests='{"hiking": true, "dining": true, "movies": true, "study": true}',
                profile_image=f'https://ui-avatars.com/api/?name={netid}&background=orange&color=fff',
                password_hash=secrets.token_hex(16)
            )
            db.session.add(new_user)
            db.session.commit()
            
            # Retrieve the user after commit
            user = User.query.filter_by(netid=netid).first()
        elif not user.netid or not user.cas_id:
            # If we have a user but they're missing netid or cas_id, update them
            if not user.netid:
                user.netid = netid
            if not user.cas_id:
                user.cas_id = cas_id
            db.session.commit()
        
        # Generate token for the frontend
        access_token = jwt.encode({
            'sub': user.id,
            'username': netid,
            'exp': datetime.now(timezone.utc) + timedelta(days=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        refresh_token = jwt.encode({
            'sub': user.id,
            'exp': datetime.now(timezone.utc) + timedelta(days=30)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        # Get onboarding status to pass to frontend
        needs_onboarding = not user.onboarding_completed
        
        # For Heroku environment, redirect to the frontend with the onboarding status
        if 'herokuapp.com' in request.host or os.environ.get('PRODUCTION') == 'true':
            # Use relative URL for redirect in production
            return redirect(f"/swipe?needs_onboarding={str(needs_onboarding).lower()}")
        
        # For local development, use the full URL with domain
        return redirect(f"{frontend_url}/swipe?needs_onboarding={str(needs_onboarding).lower()}")
    except Exception as e:
        print(f"CAS callback error: {str(e)}")
        return jsonify({'detail': f'Error: {str(e)}'}), 500

@app.route('/api/cas/logout', methods=['GET'])
def cas_logout():
    """Log out user from CAS"""
    # Clear the session
    session.clear()
    
    # Determine the frontend URL based on the environment
    if 'herokuapp.com' in request.host:
        # In production (Heroku), use the same host with https
        frontend_url = f"https://{request.host}"
    else:
        # In development, get from Origin header or use localhost:3000 as fallback
        frontend_url = request.headers.get('Origin', 'http://localhost:3000')
    
    # Redirect to the root URL after logout, let frontend handle the routing
    redirect_url = f"{frontend_url}/"
    logout_url = f"{_CAS_URL}logout?service={quote(redirect_url)}"
    
    # Return the logout URL to the frontend so it can redirect
    return jsonify({
        'detail': 'Logged out successfully',
        'logout_url': logout_url
    })

@app.route('/api/cas/status', methods=['GET'])
def cas_status():
    """Check if user is authenticated with CAS"""
    is_auth = is_authenticated()
    return jsonify({'authenticated': is_auth})

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
                'created_at': user.created_at.isoformat() if user.created_at else None
            })
        
        elif request.method == 'PUT':
            # Update user profile data
            data = request.json
            
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
            
            db.session.commit()
            
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
                'created_at': user.created_at.isoformat() if user.created_at else None
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
        
        # Update user data from request if provided
        if request.json:
            data = request.json
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
            # Handle prompt responses
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
        
        # Mark onboarding as completed
        user.onboarding_completed = True
        db.session.commit()
        
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
                'onboarding_completed': user.onboarding_completed
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'detail': f'Error: {str(e)}'}), 500

# Added endpoints for accepting and rejecting matches
@app.route('/api/matches/<int:match_id>/accept', methods=['PUT'])
@login_required()
def accept_match(match_id, current_user_id=None):
    try:
        # Get the match
        match = Match.query.get(match_id)
        if not match:
            return jsonify({'detail': 'Match not found'}), 404
            
        # Get the experience to verify ownership
        experience = Experience.query.get(match.experience_id)
        if not experience:
            return jsonify({'detail': 'Experience not found'}), 404
            
        # Verify that the current user is either involved in the match as user1 or user2
        if current_user_id != match.user1_id and current_user_id != match.user2_id:
            return jsonify({'detail': 'You are not authorized to interact with this match'}), 403
        
        # If the user is the experience owner, they can confirm the match
        if experience.user_id == current_user_id:
            # Update match status to confirmed
            match.status = 'confirmed'
            db.session.commit()
            
            return jsonify({
                'message': 'Match accepted successfully', 
                'match': {
                    'id': match.id,
                    'status': match.status,
                    'experience_id': match.experience_id
                }
            }), 200
        else:
            return jsonify({'detail': 'Only the experience owner can accept a match'}), 403
    except Exception as e:
        print(f"Error accepting match: {e}")
        db.session.rollback()
        return jsonify({'detail': str(e)}), 500

@app.route('/api/matches/<int:match_id>/reject', methods=['PUT'])
@login_required()
def reject_match(match_id, current_user_id=None):
    try:
        # Get the match
        match = Match.query.get(match_id)
        if not match:
            return jsonify({'detail': 'Match not found'}), 404
            
        # Get the experience to verify ownership
        experience = Experience.query.get(match.experience_id)
        if not experience:
            return jsonify({'detail': 'Experience not found'}), 404
            
        # Verify that the current user is either involved in the match as user1 or user2
        if current_user_id != match.user1_id and current_user_id != match.user2_id:
            return jsonify({'detail': 'You are not authorized to interact with this match'}), 403
        
        # Any user involved in the match can reject it
        # Delete the match
        db.session.delete(match)
        db.session.commit()
        
        return jsonify({'message': 'Match rejected successfully'}), 200
    except Exception as e:
        print(f"Error rejecting match: {e}")
        db.session.rollback()
        return jsonify({'detail': str(e)}), 500

# Catch-all routes to handle React Router paths
@app.route('/<path:path>')
def catch_all(path):
    # First try to serve as a static file (CSS, JS, etc.)
    try:
        return app.send_static_file(path)
    except:
        # If not a static file, serve the index.html for client-side routing
        return app.send_static_file('index.html')

# Add specific routes for top-level client-side routes
@app.route('/swipe')
def serve_swipe():
    return app.send_static_file('index.html')

@app.route('/login')
def serve_login():
    return app.send_static_file('index.html')

@app.route('/profile')
def serve_profile():
    return app.send_static_file('index.html')

@app.route('/experiences')
def serve_experiences():
    return app.send_static_file('index.html')

@app.route('/matches')
def serve_matches():
    return app.send_static_file('index.html')

# Function to check if profile_image column exists in the user table
def check_profile_image_column():
    try:
        conn = sqlite3.connect('dateabase.db')
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'profile_image' not in column_names:
            print("Adding profile_image column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN profile_image TEXT;")
            conn.commit()
            print("profile_image column added successfully")
        else:
            print("profile_image column already exists")
            
        conn.close()
    except Exception as e:
        print(f"Error checking profile_image column: {e}")

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