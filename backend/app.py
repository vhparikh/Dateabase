from flask import Flask, request, jsonify, send_from_directory, redirect, session, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
import os
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import secrets
import json
from urllib.parse import quote_plus, urlencode, quote
from sqlalchemy import inspect
from sqlalchemy.sql import text
try:
    from backend.auth import validate, is_authenticated, get_cas_login_url, logout_cas, strip_ticket, _CAS_URL
except ImportError:
    # For local development
    try:
        from auth import validate, is_authenticated, get_cas_login_url, logout_cas, strip_ticket, _CAS_URL
    except ImportError:
        # Mock auth functions for deployment if they don't exist
        validate = lambda *args, **kwargs: True
        is_authenticated = lambda *args, **kwargs: True
        get_cas_login_url = lambda *args, **kwargs: "/login"
        logout_cas = lambda *args, **kwargs: None
        strip_ticket = lambda *args, **kwargs: None
        _CAS_URL = "https://cas.princeton.edu/cas"

app = Flask(__name__, static_folder='../frontend/build', static_url_path='')
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

# Simple test route
@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'database_url': app.config['SQLALCHEMY_DATABASE_URI'].split('@')[1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else 'sqlite',
        'timestamp': datetime.now().isoformat()
    })

# Serve frontend static files
@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    # If the path exists in the static folder, serve it
    file_path = os.path.join(app.static_folder, path)
    if os.path.isfile(file_path):
        return send_from_directory(app.static_folder, path)
    # Otherwise, return the index.html for client-side routing
    return send_from_directory(app.static_folder, 'index.html')

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    class_year = db.Column(db.Integer, nullable=False)
    interests = db.Column(db.Text, nullable=False)  # Store as JSON string
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
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({'detail': 'Invalid credentials'}), 401
            
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
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'detail': str(e)}), 500

@app.route('/api/token/refresh', methods=['POST'])
def refresh_token():
    data = request.json
    refresh = data.get('refresh')
    
    if not refresh:
        return jsonify({'detail': 'Please provide refresh token'}), 400
    
    try:
        user_id = decode_token(refresh)
        
        if isinstance(user_id, str) and ('expired' in user_id.lower() or 'invalid' in user_id.lower()):
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
            'access': access_token
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
        
        # Handle dummy experiences (IDs 998, 999)
        if experience_id in [998, 999]:
            # For dummy experiences, create a fake match if it's a right swipe
            if direction:
                return jsonify({'match': True, 'match_id': 9999}), 200
            else:
                return jsonify({'match': False}), 200
                
        # Proceed with normal flow for real experiences
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
        
        # If no experiences are available, reset the demo state to show all experiences
        if not available_experiences:
            # For demo purposes, clear all user swipes to let them see experiences again
            UserSwipe.query.filter_by(user_id=user_id).delete()
            db.session.commit()
            # Reload experiences
            experiences = Experience.query.filter(Experience.user_id != user_id).all()
            available_experiences = experiences
            
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
        
        # If still no recommendations available, create some dummy experiences for demo
        if not result:
            # Create dummy experiences with the first user that's not the current user
            other_users = User.query.filter(User.id != user_id).all()
            if other_users:
                other_user = other_users[0]
                dummy_experiences = [
                    {
                        'id': 999,
                        'user_id': other_user.id,
                        'creator': {
                            'id': other_user.id,
                            'username': other_user.username,
                            'name': other_user.name,
                            'profile_image': other_user.profile_image if hasattr(other_user, 'profile_image') else None
                        },
                        'experience_type': 'Coffee',
                        'location': 'Local Cafe',
                        'description': 'Meeting for coffee and conversation',
                        'latitude': 40.3431,
                        'longitude': -74.6551,
                        'place_id': None,
                        'location_image': 'https://source.unsplash.com/random/800x600/?cafe',
                        'created_at': datetime.now().isoformat()
                    },
                    {
                        'id': 998,
                        'user_id': other_user.id,
                        'creator': {
                            'id': other_user.id,
                            'username': other_user.username,
                            'name': other_user.name,
                            'profile_image': other_user.profile_image if hasattr(other_user, 'profile_image') else None
                        },
                        'experience_type': 'Hike',
                        'location': 'Princeton Nature Trail',
                        'description': 'Relaxing afternoon hike through scenic trails',
                        'latitude': 40.3431,
                        'longitude': -74.6551,
                        'place_id': None,
                        'location_image': 'https://source.unsplash.com/random/800x600/?hiking',
                        'created_at': datetime.now().isoformat()
                    }
                ]
                result.extend(dummy_experiences)
        
        return jsonify(result)
    except Exception as e:
        print(f"Error fetching recommendations: {e}")
        return jsonify({'error': str(e)}), 500

def init_postgres_db():
    """Initialize the PostgreSQL database with the necessary tables"""
    try:
        # Create all tables
        db.create_all()
        print("All database tables created successfully!")
        
        # Check if any users exist
        if User.query.count() == 0:
            print("No users found. Creating a default admin user...")
            admin_user = User(
                username='admin',
                name='Admin User',
                gender='Other',
                class_year=2024,
                interests='{}',
                profile_image='https://ui-avatars.com/api/?name=Admin+User&background=red&color=fff',
                onboarding_completed=True
            )
            admin_user.set_password('admin123')  # Change this password in production
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created successfully")
        else:
            print(f"Database already has {User.query.count()} users")
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.session.rollback()

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
    """Create database tables if they don't exist"""
    try:
        db.create_all()
        print("All database tables created successfully")
        
        # Check if the onboarding_completed column exists in User table
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]
        
        if 'onboarding_completed' not in columns:
            print("Adding onboarding_completed column to User table")
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE "user" ADD COLUMN onboarding_completed BOOLEAN DEFAULT FALSE'))
                conn.commit()
    except Exception as e:
        print(f"Error creating tables: {e}")

# Initialize database
with app.app_context():
    try:
        print("Creating database tables...")
        db.create_all()
        print("Tables created successfully")
        
        # Seed demo data
        init_postgres_db()
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
        
        # Check if user exists in our database
        user = User.query.filter_by(username=netid).first()
        
        # If user doesn't exist, we'll create one with dummy data
        if not user:
            # Create a new user with the netid and dummy data
            new_user = User(
                username=netid,
                name=f"{netid.capitalize()} User",
                gender='Other',
                class_year=2025,
                interests='{"hiking": true, "dining": true, "movies": true, "study": true}',
                profile_image=f'https://ui-avatars.com/api/?name={netid}&background=orange&color=fff',
                password_hash=generate_password_hash(f"cas_{netid}_{secrets.token_hex(16)}") # Generate a random secure password
            )
            db.session.add(new_user)
            db.session.commit()
            
            # Retrieve the user after commit
            user = User.query.filter_by(username=netid).first()
        
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

# Get current user profile - checks for CAS authentication only
@app.route('/api/users/me', methods=['GET'])
def get_current_user():
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return jsonify({'detail': 'Missing authorization header'}), 401
    
    try:
        # Extract the token
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        user_id = decode_token(token)
        
        if isinstance(user_id, str) and ('expired' in user_id.lower() or 'invalid' in user_id.lower()):
            return jsonify({'detail': user_id}), 401
        
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'detail': 'User not found'}), 404
        
        return jsonify({
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'gender': user.gender,
            'class_year': user.class_year,
            'interests': user.interests,
            'profile_image': user.profile_image,
            'onboarding_completed': user.onboarding_completed
        })
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

# Endpoint to complete onboarding
@app.route('/api/users/complete-onboarding', methods=['POST'])
def complete_onboarding():
    """Mark user's onboarding as completed"""
    try:
        # Check if user is authenticated via CAS
        if 'user_info' in session:
            user_info = session['user_info']
            netid = user_info.get('user', '')
            
            # Find the user by netid
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
                    'name': user.name,
                    'gender': user.gender,
                    'class_year': user.class_year,
                    'interests': user.interests,
                    'profile_image': user.profile_image,
                    'onboarding_completed': user.onboarding_completed
                }
            })
        
        # Not authenticated with CAS
        return jsonify({'detail': 'Authentication required'}), 401
    except Exception as e:
        db.session.rollback()
        return jsonify({'detail': f'Error: {str(e)}'}), 500

if __name__ == '__main__':
    with app.app_context():
        create_tables()
        check_profile_image_column()
        init_postgres_db()  # Initialize PostgreSQL database
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 