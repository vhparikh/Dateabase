from flask import Flask, request, jsonify, send_from_directory, redirect, session, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
import os
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import secrets
from urllib.parse import quote_plus, urlencode, quote
from auth import validate, is_authenticated, get_cas_login_url, logout_cas, strip_ticket, _CAS_URL

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Database configuration
db_url = os.environ.get('DATABASE_URL', 'sqlite:///dateabase.db')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')
# Set session type for CAS auth
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=True)  # Made nullable for CAS users
    cas_id = db.Column(db.String(50), unique=True, nullable=True)  # CAS unique identifier
    netid = db.Column(db.String(50), unique=True, nullable=True)  # Princeton NetID
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(20), nullable=True)  # Made nullable for initial CAS login
    class_year = db.Column(db.Integer, nullable=True)  # Made nullable for initial CAS login
    interests = db.Column(db.Text, nullable=True)  # Made nullable for initial CAS login
    profile_image = db.Column(db.Text, nullable=True)  # URL to profile image
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    onboarding_completed = db.Column(db.Boolean, default=False)  # Track if user has completed onboarding
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Experience(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    experience_type = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    place_id = db.Column(db.String(255), nullable=True)
    location_image = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('experiences', lazy=True))

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    experience_id = db.Column(db.Integer, db.ForeignKey('experience.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending' or 'confirmed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user1 = db.relationship('User', foreign_keys=[user1_id])
    user2 = db.relationship('User', foreign_keys=[user2_id])
    experience = db.relationship('Experience')

class UserSwipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    experience_id = db.Column(db.Integer, db.ForeignKey('experience.id'), nullable=False)
    direction = db.Column(db.Boolean, nullable=False)  # True for right, False for left
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User')
    experience = db.relationship('Experience')

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
    
    if not refresh:
        return jsonify({'detail': 'Refresh token is required'}), 400
    
    try:
        # Decode the refresh token to get the user ID
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
        
        if 'name' in data:
            user.name = data['name']
        if 'gender' in data:
            user.gender = data['gender']
        if 'class_year' in data:
            user.class_year = data['class_year']
        if 'interests' in data:
            user.interests = data['interests']
        if 'profile_image' in data:
            user.profile_image = data['profile_image']
        if 'password' in data:
            user.set_password(data['password'])
            
        db.session.commit()
        
        return jsonify({
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'gender': user.gender,
            'class_year': user.class_year,
            'interests': user.interests,
            'profile_image': user.profile_image,
            'message': 'User updated successfully'
        })
    except Exception as e:
        print(f"Error updating user: {e}")
        db.session.rollback()
        return jsonify({'detail': str(e)}), 500

@app.route('/api/experiences', methods=['POST'])
def create_experience():
    try:
        data = request.json
        
        if not data:
            return jsonify({'detail': 'No data provided'}), 400
        
        required_fields = ['user_id', 'experience_type', 'location']
        for field in required_fields:
            if field not in data:
                return jsonify({'detail': f'Missing required field: {field}'}), 400
                
        # Validate user exists
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'detail': 'User not found'}), 404
        
        # Clean up input data to prevent duplication
        experience_type = data['experience_type'].strip() if data['experience_type'] else ''
        location = data['location'].strip() if data['location'] else ''
        description = data.get('description', '').strip()
        
        # Handle new fields
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        place_id = data.get('place_id', '').strip() if data.get('place_id') else None
        location_image = data.get('location_image', '').strip() if data.get('location_image') else None
        
        new_experience = Experience(
            user_id=data['user_id'],
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
        db.session.rollback()
        return jsonify({'detail': str(e)}), 500

@app.route('/api/experiences', methods=['GET'])
def get_experiences():
    try:
        experiences = Experience.query.all()
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

@app.route('/api/swipes', methods=['POST'])
def create_swipe():
    try:
        data = request.json
        print(f"Received swipe data: {data}")
        
        # Extract required fields
        user_id = data.get('user_id')
        experience_id = data.get('experience_id')
        direction = data.get('direction')
        
        # Validate required fields
        if not all([user_id, experience_id, direction is not None]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Convert direction to boolean
        if isinstance(direction, str):
            # Handle string representations of direction
            direction_lower = direction.lower()
            if direction_lower in ['true', 'right', 'like', '1', 'yes']:
                direction = True
            elif direction_lower in ['false', 'left', 'pass', '0', 'no']:
                direction = False
            else:
                return jsonify({'error': f'Invalid direction value: {direction}'}), 400
        else:
            # Ensure it's a boolean
            direction = bool(direction)
            
        print(f"Processed swipe: User {user_id}, Experience {experience_id}, Direction {direction}")
        
        # Proceed with normal flow for experiences
        # Find the experience to ensure it exists
        experience = Experience.query.get(experience_id)
        if not experience:
            return jsonify({'error': 'Experience not found'}), 404
            
        # Create the swipe record
        new_swipe = UserSwipe(
            user_id=user_id,
            experience_id=experience_id,
            direction=direction
        )
        db.session.add(new_swipe)
        db.session.commit()
        
        # Check if this creates a match
        if direction:  # If right swipe
            # Find if the experience creator also swiped right on this user
            print(f"Checking for match with creator {experience.user_id}")
            
            # Check if the current user has an experience that the creator liked
            user_experiences = Experience.query.filter_by(user_id=user_id).all()
            user_exp_ids = [exp.id for exp in user_experiences]
            
            creator_swipes = UserSwipe.query.filter(
                UserSwipe.user_id == experience.user_id,
                UserSwipe.experience_id.in_(user_exp_ids),
                UserSwipe.direction == True
            ).all()
            
            if creator_swipes:
                print(f"Match found between {user_id} and {experience.user_id}")
                # Check if match already exists
                existing_match = Match.query.filter(
                    ((Match.user1_id == user_id) & (Match.user2_id == experience.user_id)) |
                    ((Match.user1_id == experience.user_id) & (Match.user2_id == user_id))
                ).first()
                
                if existing_match:
                    print(f"Match already exists with ID {existing_match.id}")
                    return jsonify({'match': True, 'match_id': existing_match.id}), 200
                
                # Create a match
                new_match = Match(
                    user1_id=user_id,
                    user2_id=experience.user_id,
                    experience_id=experience_id,
                    status='confirmed'
                )
                db.session.add(new_match)
                db.session.commit()
                return jsonify({'match': True, 'match_id': new_match.id}), 201
        
        return jsonify({'success': True}), 200
    except Exception as e:
        print(f"Error processing swipe: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/matches/<int:user_id>', methods=['GET'])
def get_matches(user_id):
    try:
        matches = Match.query.filter(
            ((Match.user1_id == user_id) | (Match.user2_id == user_id)) & 
            (Match.status == 'confirmed')
        ).all()
        
        result = []
        for match in matches:
            other_user_id = match.user2_id if match.user1_id == user_id else match.user1_id
            other_user = User.query.get(other_user_id)
            experience = Experience.query.get(match.experience_id)
            
            if not other_user or not experience:
                continue
                
            result.append({
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
                    'location_image': experience.location_image
                },
                'created_at': match.created_at.isoformat() if match.created_at else None,
                'status': match.status
            })
        
        return jsonify(result)
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

# DEMO CODE REMOVED
# @app.route('/api/demo/refresh', methods=['POST'])
# def refresh_demo_user():
#     """Reset the demo user's swipes and recreate demo matches"""
#     try:
#         # Get the demo user
#         demo_user = User.query.filter_by(username='demo_user').first()
#         
#         if not demo_user:
#             return jsonify({'error': 'Demo user not found'}), 404
#             
#         # Delete all swipes by the demo user
#         UserSwipe.query.filter_by(user_id=demo_user.id).delete()
#         
#         # Delete all matches involving the demo user
#         Match.query.filter(
#             (Match.user1_id == demo_user.id) | (Match.user2_id == demo_user.id)
#         ).delete()
#         
#         db.session.commit()
#         
#         # Recreate demo matches
#         create_demo_matches()
#         
#         return jsonify({'message': 'Demo user swipes and matches refreshed successfully'}), 200
#     except Exception as e:
#         print(f"Error refreshing demo user: {e}")
#         db.session.rollback()
#         return jsonify({'error': str(e)}), 500

# DEMO CODE REMOVED
# def seed_demo_data():
#     """Seed demo users and experiences if they don't exist already"""
#     try:
#         # Check if demo user exists
#         demo_user = User.query.filter_by(username='demo_user').first()
#         
#         if not demo_user:
#             print("Creating demo user...")
#             demo_user = User(
#                 username='demo_user',
#                 name='Demo User',
#                 gender='Other',
#                 class_year=2024,
#                 interests='{"hiking": true, "dining": true, "movies": true, "study": true}',
#                 profile_image='https://ui-avatars.com/api/?name=Demo+User&background=orange&color=fff'
#             )
#             demo_user.set_password('demo123')
#             db.session.add(demo_user)
#             db.session.commit()  # Commit first to get the user ID
#             
#             # Get the demo user's actual ID
#             demo_user = User.query.filter_by(username='demo_user').first()
#             
#             # Add experiences for the demo user
#             experiences = [
#                 Experience(
#                     user_id=demo_user.id,
#                     experience_type='Dining',
#                     location='Prospect Garden',
#                     description='Picnic under the cherry blossoms',
#                     latitude=40.3465,
#                     longitude=-74.6514,
#                     location_image='https://source.unsplash.com/random/800x600/?garden+princeton'
#                 ),
#                 Experience(
#                     user_id=demo_user.id,
#                     experience_type='Study',
#                     location='Firestone Library',
#                     description='Late night study session with coffee',
#                     latitude=40.3500,
#                     longitude=-74.6572,
#                     location_image='https://source.unsplash.com/random/800x600/?library+princeton'
#                 ),
#                 Experience(
#                     user_id=demo_user.id,
#                     experience_type='Activity',
#                     location='Lake Carnegie',
#                     description='Morning rowing and watching the sunrise',
#                     latitude=40.3353,
#                     longitude=-74.6389,
#                     location_image='https://source.unsplash.com/random/800x600/?lake+princeton'
#                 )
#             ]
#             
#             for exp in experiences:
#                 db.session.add(exp)
#                 
#             db.session.commit()
#             print("Demo user experiences created")
#         else:
#             print(f"Demo user already exists with ID: {demo_user.id}")
#             
#         # Check if other users exist
#         alex = User.query.filter_by(username='alex23').first()
#         if not alex:
#             alex = User(
#                 username='alex23',
#                 name='Alex Johnson',
#                 gender='Male',
#                 class_year=2023,
#                 interests='{"coffee": true, "music": true, "hiking": true}',
#                 profile_image='https://ui-avatars.com/api/?name=Alex+Johnson&background=blue&color=fff'
#             )
#             alex.set_password('pass123')
#             db.session.add(alex)
#             # Commit to get the user ID
#             db.session.commit()
#             print("User alex23 created")
#             
#             # Now add experiences for Alex
#             alex_experiences = [
#                 Experience(
#                     user_id=alex.id,
#                     experience_type='Coffee',
#                     location='Small World Coffee',
#                     description='Morning coffee date with good conversation',
#                     latitude=40.3507,
#                     longitude=-74.6604,
#                     location_image='https://source.unsplash.com/random/800x600/?coffee+shop'
#                 ),
#                 Experience(
#                     user_id=alex.id,
#                     experience_type='Hiking',
#                     location='Mountain Lakes Preserve',
#                     description='Afternoon hike through the woods',
#                     latitude=40.3704,
#                     longitude=-74.6728,
#                     location_image='https://source.unsplash.com/random/800x600/?hiking+trail'
#                 )
#             ]
#             
#             for exp in alex_experiences:
#                 db.session.add(exp)
#             db.session.commit()
#         else:
#             print("User alex23 already exists")
#             
#         emma = User.query.filter_by(username='emma_p').first()
#         if not emma:
#             emma = User(
#                 username='emma_p',
#                 name='Emma Parker',
#                 gender='Female',
#                 class_year=2025,
#                 interests='{"art": true, "dining": true, "movies": true}',
#                 profile_image='https://ui-avatars.com/api/?name=Emma+Parker&background=purple&color=fff'
#             )
#             emma.set_password('pass123')
#             db.session.add(emma)
#             # Commit to get the user ID
#             db.session.commit()
#             
#             # Add experiences for Emma
#             emma_experiences = [
#                 Experience(
#                     user_id=emma.id,
#                     experience_type='Movie',
#                     location='Princeton Garden Theatre',
#                     description='Classic film night followed by dessert',
#                     latitude=40.3499,
#                     longitude=-74.6589,
#                     location_image='https://source.unsplash.com/random/800x600/?movie+theater'
#                 ),
#                 Experience(
#                     user_id=emma.id,
#                     experience_type='Art',
#                     location='Princeton University Art Museum',
#                     description='Exploring art exhibits followed by coffee',
#                     latitude=40.3463,
#                     longitude=-74.6577,
#                     location_image='https://source.unsplash.com/random/800x600/?art+museum'
#                 )
#             ]
#             
#             for exp in emma_experiences:
#                 db.session.add(exp)
#             db.session.commit()
#         else:
#             print("User emma_p already exists")
#             
#         taylor = User.query.filter_by(username='taylor_m').first()
#         if not taylor:
#             taylor = User(
#                 username='taylor_m',
#                 name='Taylor Mitchell',
#                 gender='Non-binary',
#                 class_year=2024,
#                 interests='{"music": true, "tech": true, "food": true}',
#                 profile_image='https://ui-avatars.com/api/?name=Taylor+Mitchell&background=green&color=fff'
#             )
#             taylor.set_password('pass123')
#             db.session.add(taylor)
#             # Commit to get the user ID
#             db.session.commit()
#             
#             # Add experiences for Taylor
#             taylor_experiences = [
#                 Experience(
#                     user_id=taylor.id,
#                     experience_type='Concert',
#                     location='Richardson Auditorium',
#                     description='Chamber music concert and discussion',
#                     latitude=40.3482,
#                     longitude=-74.6595,
#                     location_image='https://source.unsplash.com/random/800x600/?concert+hall'
#                 ),
#                 Experience(
#                     user_id=taylor.id,
#                     experience_type='Dining',
#                     location='Mistral',
#                     description='Fine dining experience with seasonal menu',
#                     latitude=40.3500,
#                     longitude=-74.6611,
#                     location_image='https://source.unsplash.com/random/800x600/?fine+dining'
#                 )
#             ]
#             
#             for exp in taylor_experiences:
#                 db.session.add(exp)
#             db.session.commit()
#         else:
#             print("User taylor_m already exists")
#         
#     except Exception as e:
#         print(f"Error seeding demo user: {e}")
#         db.session.rollback()
        
#         if not demo_user:
#             print("Creating demo user...")
#             demo_user = User(
#                 username='demo_user',
#                 name='Demo User',
#                 gender='Other',
#                 class_year=2024,
#                 interests='{"hiking": true, "dining": true, "movies": true, "study": true}',
#                 profile_image='https://ui-avatars.com/api/?name=Demo+User&background=orange&color=fff'
#             )
#             demo_user.set_password('demo123')
#             db.session.add(demo_user)
#             db.session.commit()  # Commit first to get the user ID
            
#             # Get the demo user's actual ID
#             demo_user = User.query.filter_by(username='demo_user').first()
#             
#             # Add experiences for the demo user
#             experiences = [
#                 Experience(
#                     user_id=demo_user.id,
#                     experience_type='Dining',
#                     location='Prospect Garden',
#                     description='Picnic under the cherry blossoms',
#                     latitude=40.3465,
#                     longitude=-74.6514,
#                     location_image='https://source.unsplash.com/random/800x600/?garden+princeton'
#                 ),
#                 Experience(
#                     user_id=demo_user.id,
#                     experience_type='Study',
#                     location='Firestone Library',
#                     description='Late night study session with coffee',
#                     latitude=40.3500,
#                     longitude=-74.6572,
#                     location_image='https://source.unsplash.com/random/800x600/?library+princeton'
#                 ),
#                 Experience(
            # for exp in experiences:
            #     db.session.add(exp)
                
            # db.session.commit()
            # print("Demo user experiences created")
        # else:
        #     print(f"Demo user already exists with ID: {demo_user.id}")
            
        # Check if other users exist
        # alex = User.query.filter_by(username='alex23').first()
        # if not alex:
        #     alex = User(
        #         username='alex23',
        #         name='Alex Johnson',
        #         gender='Male',
        #         class_year=2023,
        #         interests='{"coffee": true, "music": true, "hiking": true}',
        #         profile_image='https://ui-avatars.com/api/?name=Alex+Johnson&background=blue&color=fff'
        #     )
        #     alex.set_password('pass123')
        #     db.session.add(alex)
        #     # Commit to get the user ID
        #     db.session.commit()
        #     print("User alex23 created")
            
        #     # Now add experiences for Alex
        #     alex_experiences = [
        #         Experience(
        #             user_id=alex.id,
        #             experience_type='Coffee',
        #             location='Small World Coffee',
        #             description='Morning coffee date with good conversation',
        #             latitude=40.3507,
        #             longitude=-74.6604,
        #             location_image='https://source.unsplash.com/random/800x600/?coffee+shop'
        #         ),
        #         Experience(
        #             user_id=alex.id,
        #             experience_type='Hiking',
        #             location='Mountain Lakes Preserve',
        #             description='Afternoon hike through the woods',
        #             latitude=40.3704,
        #             longitude=-74.6728,
        #             location_image='https://source.unsplash.com/random/800x600/?hiking+trail'
        #         )
        #     ]
            
        #     for exp in alex_experiences:
        #         db.session.add(exp)
        #     db.session.commit()
        # else:
        #     print("User alex23 already exists")
            
        # emma = User.query.filter_by(username='emma_p').first()
        # if not emma:
        #     emma = User(
        #         username='emma_p',
        #         name='Emma Parker',
        #         gender='Female',
        #         class_year=2025,
        #         interests='{"art": true, "dining": true, "movies": true}',
        #         profile_image='https://ui-avatars.com/api/?name=Emma+Parker&background=purple&color=fff'
        #     )
        #     emma.set_password('pass123')
        #     db.session.add(emma)
        #     # Commit to get the user ID
        #     db.session.commit()
            
        #     # Add experiences for Emma
        #     emma_experiences = [
        #         Experience(
        #             user_id=emma.id,
        #             experience_type='Movie',
        #             location='Princeton Garden Theatre',
        #             description='Classic film night followed by dessert',
        #             latitude=40.3499,
        #             longitude=-74.6589,
        #             location_image='https://source.unsplash.com/random/800x600/?movie+theater'
        #         ),
        #         Experience(
        #             user_id=emma.id,
        #             experience_type='Art',
        #             location='Princeton University Art Museum',
        #             description='Exploring art exhibits followed by coffee',
        #             latitude=40.3463,
        #             longitude=-74.6577,
        #             location_image='https://source.unsplash.com/random/800x600/?art+museum'
        #         )
        #     ]
            
        #     for exp in emma_experiences:
        #         db.session.add(exp)
        #     db.session.commit()
        # else:
        #     print("User emma_p already exists")
            
        # taylor = User.query.filter_by(username='taylor_m').first()
        # if not taylor:
        #     taylor = User(
        #         username='taylor_m',
        #         name='Taylor Mitchell',
        #         gender='Non-binary',
        #         class_year=2024,
        #         interests='{"music": true, "tech": true, "food": true}',
        #         profile_image='https://ui-avatars.com/api/?name=Taylor+Mitchell&background=green&color=fff'
        #     )
        #     taylor.set_password('pass123')
        #     db.session.add(taylor)
        #     # Commit to get the user ID
        #     db.session.commit()
            
        #     # Add experiences for Taylor
        #     taylor_experiences = [
        #         Experience(
        #             user_id=taylor.id,
        #             experience_type='Concert',
        #             location='Richardson Auditorium',
        #             description='Chamber music concert and discussion',
        #             latitude=40.3482,
        #             longitude=-74.6595,
        #             location_image='https://source.unsplash.com/random/800x600/?concert+hall'
        #         ),
        #         Experience(
        #             user_id=taylor.id,
        #             experience_type='Dining',
        #             location='Mistral',
        #             description='Fine dining experience with seasonal menu',
        #             latitude=40.3500,
        #             longitude=-74.6611,
        #             location_image='https://source.unsplash.com/random/800x600/?fine+dining'
        #         )
        #     ]
            
        #     for exp in taylor_experiences:
        #         db.session.add(exp)
        #     db.session.commit()
        # else:
        #     print("User taylor_m already exists")

# DEMO CODE REMOVED
# def create_demo_matches():
#     """Create some demo matches between users"""
#     try:
#         # Get users
#         demo_user = User.query.filter_by(username='demo_user').first()
#         alex = User.query.filter_by(username='alex23').first()
#         emma = User.query.filter_by(username='emma_p').first()
#         taylor = User.query.filter_by(username='taylor_m').first()
#         
#         if not (demo_user and alex and emma and taylor):
#             print("Cannot create matches: missing users")
#             return
#         
#         # Check for existing matches to avoid duplicates
#         existing_matches = Match.query.filter(
#             ((Match.user1_id == demo_user.id) & (Match.user2_id == alex.id)) |
#             ((Match.user1_id == alex.id) & (Match.user2_id == demo_user.id))
#         ).first()
#         
#         if not existing_matches:
#             # Get one experience from Alex to match with
#             alex_exp = Experience.query.filter_by(user_id=alex.id).first()
#             if alex_exp:
#                 # Create a match between demo_user and alex
#                 match1 = Match(
#                     user1_id=demo_user.id,
#                     user2_id=alex.id,
#                     experience_id=alex_exp.id,
#                     status='confirmed'
#                 )
#                 db.session.add(match1)
#                 print(f"Created match between Demo User and Alex")
#             
#         # Check for match between demo_user and emma
#         existing_matches = Match.query.filter(
#             ((Match.user1_id == demo_user.id) & (Match.user2_id == emma.id)) |
#             ((Match.user1_id == emma.id) & (Match.user2_id == demo_user.id))
#         ).first()
#         
#         if not existing_matches:
#             # Get one experience from Emma to match with
#             emma_exp = Experience.query.filter_by(user_id=emma.id).first()
#             if emma_exp:
#                 # Create a match between demo_user and emma
#                 match2 = Match(
#                     user1_id=demo_user.id,
#                     user2_id=emma.id,
#                     experience_id=emma_exp.id,
#                     status='confirmed'
#                 )
#                 db.session.add(match2)
#                 print(f"Created match between Demo User and Emma")
#         
#         # Check for match between alex and taylor
#         existing_matches = Match.query.filter(
#             ((Match.user1_id == alex.id) & (Match.user2_id == taylor.id)) |
#             ((Match.user1_id == taylor.id) & (Match.user2_id == alex.id))
#         ).first()
#         
#         if not existing_matches:
#             # Get one experience from Taylor to match with
#             taylor_exp = Experience.query.filter_by(user_id=taylor.id).first()
#             if taylor_exp:
#                 # Create a match between alex and taylor
#                 match3 = Match(
#                     user1_id=alex.id,
#                     user2_id=taylor.id,
#                     experience_id=taylor_exp.id,
#                     status='confirmed'
#                 )
#                 db.session.add(match3)
#                 print(f"Created match between Alex and Taylor")
#         
#         # Check for match between emma and taylor
#         existing_matches = Match.query.filter(
#             ((Match.user1_id == emma.id) & (Match.user2_id == taylor.id)) |
#             ((Match.user1_id == taylor.id) & (Match.user2_id == emma.id))
#         ).first()
#         
#         if not existing_matches:
#             # Get one experience from Emma to match with
#             emma_exp = Experience.query.filter_by(user_id=emma.id).first()
#             if emma_exp:
#                 # Create a match between emma and taylor
#                 match4 = Match(
#                     user1_id=emma.id,
#                     user2_id=taylor.id,
#                     experience_id=emma_exp.id,
#                     status='confirmed'
#                 )
#                 db.session.add(match4)
#                 print(f"Created match between Emma and Taylor")
#                 
#         db.session.commit()
#         print("Demo matches created successfully")
#         
#     except Exception as e:
#         print(f"Error creating demo matches: {e}")
#         db.session.rollback()
# DEMO CODE REMOVED - MATCH CREATION CODE

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
        
        # Get the frontend URL from the Origin header or use localhost:3000 as fallback
        frontend_url = request.headers.get('Origin', 'http://localhost:3000')
        frontend_callback = f"{frontend_url}/cas/callback"
        
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
                password_hash=generate_password_hash(f"cas_{netid}_{secrets.token_hex(16)}") # Generate a random secure password
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
        
        # Redirect to the frontend callback with the ticket and onboarding status
        redirect_url = f"{frontend_callback}?ticket={ticket}&needs_onboarding={str(needs_onboarding).lower()}"
        return redirect(redirect_url)
    except Exception as e:
        return jsonify({'detail': f'Error: {str(e)}'}), 500

@app.route('/api/cas/logout', methods=['GET'])
def cas_logout():
    """Log out user from CAS"""
    # Clear the session
    session.clear()
    # Create CAS logout URL that redirects back to the login page
    frontend_url = request.headers.get('Origin', 'http://localhost:3000')
    redirect_url = f"{frontend_url}/login"
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
                'class_year': user.class_year,
                'interests': user.interests,
                'profile_image': user.profile_image,
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
            if 'class_year' in data:
                user.class_year = data['class_year']
            if 'interests' in data:
                user.interests = data['interests']
            if 'profile_image' in data:
                user.profile_image = data['profile_image']
            
            db.session.commit()
            
            # Return updated user profile
            return jsonify({
                'id': user.id,
                'username': user.username,
                'netid': user.netid,
                'name': user.name,
                'gender': user.gender,
                'class_year': user.class_year,
                'interests': user.interests,
                'profile_image': user.profile_image,
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
        
        # Find the user by netid first, then by username as fallback
        user = User.query.filter_by(netid=netid).first()
        if not user:
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
            if 'class_year' in data:
                user.class_year = data['class_year']
            if 'interests' in data:
                user.interests = data['interests']
            if 'profile_image' in data:
                user.profile_image = data['profile_image']
        
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
                'class_year': user.class_year,
                'interests': user.interests,
                'profile_image': user.profile_image,
                'onboarding_completed': user.onboarding_completed
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'detail': f'Error: {str(e)}'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Removed demo data seeding
    app.run(debug=True, port=5001) 