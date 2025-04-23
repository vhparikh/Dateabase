from flask import Flask, request, jsonify, send_from_directory, redirect, session, url_for
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
import os
import jwt
import secrets
import google.generativeai as genai
import cloudinary
import cloudinary.uploader
import cloudinary.api
from urllib.parse import quote_plus, urlencode, quote
import pinecone
import numpy as np
import json
import cohere  # Import Cohere client
from sqlalchemy import text

# Embedding function using Cohere API
def get_embedding(text):
    """Generate embeddings using Cohere's embedding API"""
    try:
        # Get API key from environment variable
        api_key = os.environ.get("COHERE_API_KEY")
        if not api_key:
            print("ERROR: COHERE_API_KEY environment variable not set")
            # Return dummy vector as fallback
            print("Using fallback dummy vector of 1024 dimensions")
            return [0.1] * 1024
            
        # Initialize Cohere client
        co = cohere.Client(api_key)
        
        # Generate embedding using Cohere's API
        print(f"Generating embedding via Cohere API for text: {text[:50]}...")
        response = co.embed(
            texts=[text],
            model="embed-english-v3.0",
            input_type="search_document"
        )
        
        # Extract the embedding from the response
        embedding = response.embeddings[0]
        
        # Verify embedding dimension
        embedding_dim = len(embedding)
        print(f"Generated embedding with dimension {embedding_dim}")
        
        # Cohere's embed-english-v3.0 model produces 1024-dimensional vectors,
        # which matches our Pinecone index perfectly
        assert embedding_dim == 1024, f"Embedding dimension mismatch: {embedding_dim} != 1024"
        
        return embedding
        
    except Exception as e:
        print(f"Error generating embedding with Cohere API: {e}")
        # Return dummy vector as fallback
        print("Using fallback dummy vector of 1024 dimensions")
        return [0.1] * 1024

try:
    # Try local import first (for local development)
    from auth import validate, is_authenticated, get_cas_login_url, logout_cas, strip_ticket, _CAS_URL
    from database import db, init_db, User, Experience, Match, UserSwipe, UserImage, add_new_columns, drop_unused_columns
except ImportError:
    # Fall back to package import (for Heroku)
    from backend.auth import validate, is_authenticated, get_cas_login_url, logout_cas, strip_ticket, _CAS_URL
    from backend.database import db, init_db, User, Experience, Match, UserSwipe, UserImage, add_new_columns, drop_unused_columns
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

# Configure Gemini API key
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Configure Pinecone
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY', '')
PINECONE_ENV = os.environ.get('PINECONE_ENV', '')
# Check for both variable names since Heroku has PINECONE_INDEX_NAME
PINECONE_INDEX = os.environ.get('PINECONE_INDEX', '') or os.environ.get('PINECONE_INDEX_NAME', '')

# Initialize Pinecone if we have the required environment variables
pinecone_initialized = False
pinecone_index = None

if PINECONE_API_KEY and PINECONE_INDEX:
    try:
        # Updated initialization pattern for Pinecone
        import pinecone
        pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
        pinecone_index = pc.Index(PINECONE_INDEX)
        pinecone_initialized = True
        print(f"Pinecone initialized with index: {PINECONE_INDEX}")
    except Exception as e:
        print(f"Error initializing Pinecone: {e}")
else:
    print("Pinecone environment variables not set. Vector search functionality unavailable.")
    if not PINECONE_API_KEY:
        print("PINECONE_API_KEY is missing")
    if not PINECONE_INDEX:
        print("Both PINECONE_INDEX and PINECONE_INDEX_NAME are missing")

# Configure Cloudinary
CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL', '')
if CLOUDINARY_URL:
    cloudinary.config(secure=True)
else:
    print("Warning: CLOUDINARY_URL not set. Image uploads will not work.")

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

# Helper function to convert user preferences to a text description for embedding
def get_user_preference_text(user):
    """
    Generate a comprehensive text description of user preferences including explicit preferences
    from their profile and implicit preferences from their swipe history.
    
    This richer representation will be used to generate a more accurate embedding vector.
    """
    preference_parts = []
    
    # EXPLICIT PREFERENCES FROM USER PROFILE
    
    # Add gender preference
    if user.gender_pref:
        preference_parts.append(f"Gender preference: {user.gender_pref}")
    
    # Add experience type preferences
    if user.experience_type_prefs:
        try:
            exp_prefs = json.loads(user.experience_type_prefs)
            exp_types = [exp_type for exp_type, is_selected in exp_prefs.items() if is_selected]
            if exp_types:
                preference_parts.append(f"Experience types: {', '.join(exp_types)}")
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Add class year preferences
    if user.class_year_min_pref and user.class_year_max_pref:
        preference_parts.append(f"Class years: {user.class_year_min_pref} to {user.class_year_max_pref}")
    
    # Add interest preferences
    if user.interests_prefs:
        try:
            interest_prefs = json.loads(user.interests_prefs)
            interests = [interest for interest, is_selected in interest_prefs.items() if is_selected]
            if interests:
                preference_parts.append(f"Interests: {', '.join(interests)}")
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Add other user attributes that might be relevant for matching
    if user.major:
        preference_parts.append(f"Major: {user.major}")
    
    # IMPLICIT PREFERENCES FROM USER BEHAVIOR
    
    # Get experiences this user liked (swiped right)
    liked_swipes = UserSwipe.query.filter_by(user_id=user.id, direction=True).all()
    if liked_swipes:
        liked_experience_ids = [swipe.experience_id for swipe in liked_swipes]
        liked_experiences = Experience.query.filter(Experience.id.in_(liked_experience_ids)).all()
        
        # Extract patterns from liked experiences
        liked_types = {}
        liked_creators = {}
        
        for exp in liked_experiences:
            # Count experience types
            if exp.experience_type:
                exp_type = exp.experience_type.strip()
                liked_types[exp_type] = liked_types.get(exp_type, 0) + 1
            
            # Count creator attributes
            creator = User.query.get(exp.user_id)
            if creator:
                # Count creator classes
                if creator.class_year:
                    liked_creators[f"class_{creator.class_year}"] = liked_creators.get(f"class_{creator.class_year}", 0) + 1
                
                # Count creator genders
                if creator.gender:
                    liked_creators[f"gender_{creator.gender}"] = liked_creators.get(f"gender_{creator.gender}", 0) + 1
                
                # Count creator majors
                if creator.major:
                    liked_creators[f"major_{creator.major}"] = liked_creators.get(f"major_{creator.major}", 0) + 1
        
        # Add most liked experience types to preferences
        if liked_types:
            sorted_types = sorted(liked_types.items(), key=lambda x: x[1], reverse=True)
            top_types = [t[0] for t in sorted_types[:3]]  # Top 3 experience types
            if top_types:
                preference_parts.append(f"Liked experience types: {', '.join(top_types)}")
        
        # Add most liked creator attributes to preferences
        if liked_creators:
            sorted_creators = sorted(liked_creators.items(), key=lambda x: x[1], reverse=True)
            top_creator_attrs = []
            
            for attr, count in sorted_creators[:5]:  # Top 5 creator attributes
                if attr.startswith("class_"):
                    top_creator_attrs.append(f"class year {attr[6:]}")
                elif attr.startswith("gender_"):
                    top_creator_attrs.append(f"gender {attr[7:]}")
                elif attr.startswith("major_"):
                    top_creator_attrs.append(f"major {attr[6:]}")
            
            if top_creator_attrs:
                preference_parts.append(f"Preferred creator attributes: {', '.join(top_creator_attrs)}")
    
    # Join all parts into a single text description
    if preference_parts:
        return " ".join(preference_parts)
    else:
        return "No specific preferences"

# Helper function to get experience text description for embedding
def get_experience_text(experience, creator=None):
    """
    Generate a rich text description of an experience including both the experience details
    and comprehensive information about the creator.
    
    This combined representation enables searching for experiences based on both
    the experience itself and the characteristics of the person who created it.
    """
    exp_parts = []
    
    # EXPERIENCE DETAILS
    
    # Basic experience info with stronger emphasis
    if experience.experience_type:
        exp_parts.append(f"Experience type: {experience.experience_type}")
    
    if experience.location:
        exp_parts.append(f"Location: {experience.location}")
    
    if experience.description:
        exp_parts.append(f"Description: {experience.description}")
    
    # Add coordinates if available for better location matching
    if experience.latitude and experience.longitude:
        exp_parts.append(f"Coordinates: {experience.latitude}, {experience.longitude}")
    
    # CREATOR DETAILS (comprehensive profile)
    if creator:
        creator_parts = []
        
        if creator.name:
            creator_parts.append(f"Creator name: {creator.name}")
        
        if creator.gender:
            creator_parts.append(f"Creator gender: {creator.gender}")
        
        if creator.class_year:
            creator_parts.append(f"Creator class year: {creator.class_year}")
        
        if creator.major:
            creator_parts.append(f"Creator major: {creator.major}")
        
        if creator.interests:
            creator_parts.append(f"Creator interests: {creator.interests}")
        
        # Add other profile fields if available
        if hasattr(creator, 'bio') and creator.bio:
            creator_parts.append(f"Creator bio: {creator.bio}")
            
        if hasattr(creator, 'hometown') and creator.hometown:
            creator_parts.append(f"Creator hometown: {creator.hometown}")
            
        # Add creator's other experiences to provide more context
        other_experiences = Experience.query.filter_by(user_id=creator.id).filter(Experience.id != experience.id).all()
        if other_experiences:
            other_exp_types = [exp.experience_type for exp in other_experiences if exp.experience_type]
            unique_types = list(set(other_exp_types))
            if unique_types:
                creator_parts.append(f"Creator's other experience types: {', '.join(unique_types[:5])}")
        
        # Add the creator details to the experience parts
        if creator_parts:
            exp_parts.append("CREATOR PROFILE: " + " ".join(creator_parts))
    
    # Join all parts into a single text description
    if exp_parts:
        return " ".join(exp_parts)
    else:
        return "No specific experience details"

# Helper function to index an experience in Pinecone
def index_experience(experience, creator=None):
    """
    Index an experience in Pinecone for vector search.
    
    This function creates a combined vector representation of both the experience and
    its creator's profile, ensuring that personalized recommendation can consider
    both the experience itself and the person who created it.
    """
    if not pinecone_initialized or not pinecone_index:
        print(f"Experience {experience.id}: Pinecone not initialized. Cannot index experience.")
        return False
    
    try:
        # Ensure we have the creator data for better vectorization
        if not creator:
            creator = User.query.get(experience.user_id)
            if not creator:
                print(f"Experience {experience.id}: Creator not found, experience vector may be incomplete")
            else:
                print(f"Experience {experience.id}: Found creator {creator.id} ({creator.name})")
        
        # Generate text description of the experience with creator details
        text_description = get_experience_text(experience, creator)
        print(f"Experience {experience.id}: Generated text description: {text_description[:100]}...")
        
        # Create metadata for the experience
        metadata = {
            'id': experience.id,
            'user_id': experience.user_id,
            'experience_type': experience.experience_type,
            'location': experience.location,
            'description': experience.description if experience.description else "",
            'created_at': experience.created_at.isoformat() if experience.created_at else "",
        }
        
        # Add creator metadata if available
        if creator:
            metadata.update({
                'creator_name': creator.name if creator.name else "",
                'creator_gender': creator.gender if creator.gender else "",
                'creator_class_year': creator.class_year if creator.class_year else 0,
                'creator_major': creator.major if creator.major else "",
            })
            # Add more creator metadata for better matches
            if creator.hometown:
                metadata['creator_hometown'] = creator.hometown
            if creator.interests:
                metadata['creator_interests'] = creator.interests
        
        print(f"Experience {experience.id}: Created metadata")
        
        # Generate real embedding for the text description
        print(f"Experience {experience.id}: Generating embedding")
        embedding = get_embedding(text_description)
        print(f"Experience {experience.id}: Generated embedding with dimension {len(embedding)}")
        
        # Create the Pinecone vector record with real embedding
        record = {
            'id': f"exp_{experience.id}",
            'values': embedding,  # Real embedding vector
            'metadata': {
                **metadata,
                'text': text_description  # Put text in metadata
            }
        }
        
        print(f"Experience {experience.id}: Created vector record")
        
        # Upsert the record into Pinecone - updated pattern
        try:
            print(f"Experience {experience.id}: Attempting to upsert to Pinecone")
            result = pinecone_index.upsert(
                vectors=[record],
            )
            print(f"Experience {experience.id}: Successfully indexed in Pinecone. Response: {result}")
            return True
        except Exception as e:
            print(f"Experience {experience.id}: Error in Pinecone upsert operation: {e}")
            
            # Additional debug - try a simple test vector to verify connectivity
            try:
                print(f"Experience {experience.id}: Trying a simpler test vector...")
                # Create a simple test vector with the same dimension
                test_vector = {
                    "id": f"test_vector_{experience.id}",
                    "values": [0.1] * 1024,  # 1024-dimensional vector
                    "metadata": {
                        "test": True,
                        "text": "This is a test vector to verify Pinecone connectivity"
                    }
                }
                test_result = pinecone_index.upsert(vectors=[test_vector])
                print(f"Experience {experience.id}: Test vector upsert result: {test_result}")
            except Exception as test_e:
                print(f"Experience {experience.id}: Test vector also failed: {test_e}")
            
            return False
            
    except Exception as e:
        print(f"Experience {experience.id}: Error preparing data for Pinecone indexing: {e}")
        return False

# Helper function to query Pinecone with user preferences
def get_personalized_experiences(user, top_k=20):
    """
    Query Pinecone with user preferences to get highly personalized experience recommendations.
    
    This function:
    1. Uses the cached preference vector if available, or generates a new one if needed
    2. Searches for experiences with similar embeddings, considering both experience and creator attributes
    3. Returns a ranked list of experiences that best match the user's preferences
    """
    if not pinecone_initialized or not pinecone_index:
        print(f"User {user.id}: Pinecone not initialized. Cannot query for personalized experiences.")
        return None
    
    try:
        # Determine if we need to generate a new preference embedding
        # or if we can use the cached one
        preference_embedding = None
        need_new_embedding = True
        cache_new_embedding = False
        
        # Check if we have a cached preference vector
        if user.preference_vector and user.preference_vector_updated_at:
            print(f"User {user.id}: Found cached preference vector from {user.preference_vector_updated_at}")
            
            # Deserialize the cached vector from JSON
            try:
                import json
                preference_embedding = json.loads(user.preference_vector)
                vector_dimension = len(preference_embedding)
                print(f"User {user.id}: Loaded cached preference vector with dimension {vector_dimension}")
                
                # Make sure the vector has the correct dimension
                if vector_dimension == 1024:
                    # Use the cached vector - only generate a new one if the user has swiped on something
                    # since the vector was last cached
                    latest_swipe = UserSwipe.query.filter_by(user_id=user.id).order_by(
                        UserSwipe.created_at.desc()
                    ).first()
                    
                    if latest_swipe and latest_swipe.created_at > user.preference_vector_updated_at:
                        print(f"User {user.id}: Found newer swipes than cached vector, regenerating")
                        need_new_embedding = True
                        cache_new_embedding = True
                    else:
                        print(f"User {user.id}: Using cached preference vector from {user.preference_vector_updated_at}")
                        need_new_embedding = False
                else:
                    print(f"User {user.id}: Cached vector dimension mismatch: {vector_dimension} != 1024, regenerating")
                    need_new_embedding = True
                    cache_new_embedding = True
            except Exception as e:
                print(f"User {user.id}: Error loading cached preference vector: {e}")
                need_new_embedding = True
                cache_new_embedding = True
        else:
            print(f"User {user.id}: No cached preference vector found, generating new one")
            need_new_embedding = True
            cache_new_embedding = True
        
        # Generate a new preference embedding if needed
        if need_new_embedding:
            # Generate comprehensive text description of user preferences including swipe history
            preference_text = get_user_preference_text(user)
            print(f"User {user.id}: Generated preference text: {preference_text[:100]}...")
            
            # Generate embedding for user preferences using Cohere
            print(f"User {user.id}: Generating new preference embedding")
            preference_embedding = get_embedding(preference_text)
            print(f"User {user.id}: Generated preference embedding with dimension {len(preference_embedding)}")
            
            # Cache the new embedding if needed
            if cache_new_embedding:
                try:
                    import json
                    user.preference_vector = json.dumps(preference_embedding)
                    user.preference_vector_updated_at = datetime.utcnow()
                    db.session.commit()
                    print(f"User {user.id}: Cached new preference vector at {user.preference_vector_updated_at}")
                except Exception as e:
                    print(f"User {user.id}: Error caching preference vector: {e}")
                    db.session.rollback()
                    # Continue even if caching fails
        
        # Filter to exclude experiences created by the user
        # and also include any additional filtering based on user preferences
        filter_conditions = {
            "user_id": {"$ne": user.id}  # Base filter: exclude user's own experiences
        }
        
        # Add gender preference filter if specified
        if user.gender_pref and user.gender_pref != "Any":
            filter_conditions["creator_gender"] = user.gender_pref
        
        # Add class year preference filter if specified
        if user.class_year_min_pref and user.class_year_max_pref:
            filter_conditions["creator_class_year"] = {
                "$gte": user.class_year_min_pref,
                "$lte": user.class_year_max_pref
            }
        
        # For debugging, log the exact filter being used
        print(f"User {user.id}: Using Pinecone filter: {filter_conditions}")
        
        # Query Pinecone for similar vectors with enhanced filtering
        try:
            print(f"User {user.id}: Querying Pinecone with preference embedding")
            query_results = pinecone_index.query(
                top_k=top_k * 2,  # Request more results to account for filtering
                vector=preference_embedding,
                filter=filter_conditions,
                include_metadata=True
            )
            
            print(f"User {user.id}: Pinecone query returned {len(query_results.get('matches', []))} matches")
            
            # Extract and process the matching experiences
            matches = []
            for match in query_results.get('matches', []):
                exp_id = int(match['id'].split('_')[1]) if match['id'].startswith('exp_') else None
                if exp_id:
                    # Get already swiped experiences
                    already_swiped = UserSwipe.query.filter_by(
                        user_id=user.id, 
                        experience_id=exp_id
                    ).first()
                    
                    # Skip experiences the user has already swiped on
                    if already_swiped:
                        continue
                        
                    # Format the match with ID, score, and metadata
                    matches.append({
                        'id': exp_id,
                        'score': match['score'],
                        'metadata': match['metadata']
                    })
            
            # Take top_k matches after filtering
            matches = matches[:top_k]
            
            print(f"User {user.id}: Found {len(matches)} personalized experiences after filtering")
            return matches
        except Exception as query_e:
            print(f"User {user.id}: Error in Pinecone query operation: {query_e}")
            return None
            
    except Exception as e:
        print(f"User {user.id}: Error querying Pinecone for personalized experiences: {e}")
        return None

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
            print(f"User {user.id}: Preferences updated, invalidating cached preference vector")
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

@app.route('/api/experiences', methods=['POST'])
@login_required()
def create_experience(current_user_id=None):
    """Create a new experience and optionally index it in Pinecone"""
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
    
    print(f"Creating experience with type: {experience_type}, location: {location}")
    
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
                'location_image': new_experience.location_image,
                'created_at': new_experience.created_at.isoformat() if new_experience.created_at else None
            }
        }
        
        # Try to index the experience, but don't let indexing failure affect the response
        if pinecone_initialized:
            # Do the indexing in a try-except block that can't affect the main response
            try:
                print(f"Attempting to index experience {new_experience.id} in Pinecone...")
                index_result = index_experience(new_experience, user)
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
        
        # First, delete the experience from Pinecone if it's initialized
        if pinecone_initialized and pinecone_index:
            try:
                # Delete the experience from Pinecone index
                pinecone_index.delete(ids=[f"exp_{experience_id}"])
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
        
        # Get the user (creator) to update the experience in Pinecone
        user = User.query.get(current_user_id)
        
        # Update the experience in Pinecone for vector search
        if pinecone_initialized:
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
    """
    Record a user's swipe on an experience (like or dislike).
    
    If the user likes an experience, also check if the creator has liked any of the
    user's experiences to create a match.
    """
    data = request.json
    
    # Validate required fields
    if not data or 'experience_id' not in data or 'is_like' not in data:
        return jsonify({'detail': 'Missing required fields'}), 400
    
    try:
        experience_id = data['experience_id']
        is_like = data['is_like']
        
        # Check if experience exists
        experience = Experience.query.get(experience_id)
        if not experience:
            return jsonify({'detail': 'Experience not found'}), 404
        
        # Check if the user has already swiped on this experience
        existing_swipe = UserSwipe.query.filter_by(
            user_id=current_user_id,
            experience_id=experience_id
        ).first()
        
        if existing_swipe:
            # If the swipe direction is the same, just return success
            if existing_swipe.direction == is_like:
                return jsonify({'detail': 'Swipe already recorded', 'match_created': False}), 200
            
            # Otherwise, update the swipe direction
            existing_swipe.direction = is_like
            db.session.commit()
        else:
            # Record new swipe
            new_swipe = UserSwipe(
                user_id=current_user_id,
                experience_id=experience_id,
                direction=is_like
            )
            db.session.add(new_swipe)
            db.session.commit()
        
        # Invalidate the cached preference vector since the user has new swipe data
        try:
            user = User.query.get(current_user_id)
            if user and user.preference_vector:
                print(f"User {current_user_id}: Invalidating preference vector after new swipe")
                user.preference_vector_updated_at = datetime.utcnow()  # Keep the vector but mark it as needing update
                db.session.commit()
        except Exception as e:
            print(f"User {current_user_id}: Error updating preference vector timestamp: {e}")
            # Continue even if this fails
        
        # If user liked (swiped right), check for a match
        if is_like:
            # Get the creator of the experience
            creator_id = experience.user_id
            
            # Skip match checking if the creator is the same as the current user
            if creator_id == current_user_id:
                return jsonify({
                    'detail': 'Swipe recorded successfully',
                    'match_created': False
                })
            
            # Check if creator has liked any of this user's experiences
            user_experiences = Experience.query.filter_by(user_id=current_user_id).all()
            user_experience_ids = [exp.id for exp in user_experiences]
            
            if user_experience_ids:
                creator_likes = UserSwipe.query.filter(
                    UserSwipe.user_id == creator_id,
                    UserSwipe.experience_id.in_(user_experience_ids),
                    UserSwipe.direction == True
                ).first()
                
                if creator_likes:
                    # Create a match
                    new_match = Match(
                        user1_id=current_user_id,
                        user2_id=creator_id,
                        experience_id=experience_id,
                        status='pending'
                    )
                    db.session.add(new_match)
                    db.session.commit()
                    
                    # Return success with match info
                    return jsonify({
                        'detail': 'Swipe recorded successfully',
                        'match_created': True,
                        'match_id': new_match.id,
                        'match_user': {
                            'id': creator_id,
                            'name': User.query.get(creator_id).name if User.query.get(creator_id) else 'Unknown'
                        }
                    })
        
        # Return success without match
        return jsonify({
            'detail': 'Swipe recorded successfully',
            'match_created': False
        })
        
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
    """
    Return personalized experiences for the swipe interface based on user preferences
    and previous behavior.
    
    This endpoint leverages Pinecone vector search to find experiences that closely match
    the user's preference vector, combining experience attributes with creator profiles.
    
    Query parameters:
    - include_swiped: If set to "true", will include experiences the user has already swiped on,
                     enabling infinite scrolling when a user has seen all experiences.
    """
    try:
        # Get the current user
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'detail': 'User not found'}), 404
        
        # Check if we should include already swiped experiences (for infinite scrolling)
        include_swiped = request.args.get('include_swiped', 'false').lower() == 'true'
        
        print(f"User {current_user_id}: Retrieving personalized swipe experiences (include_swiped={include_swiped})")
        
        # Get experiences the user has already swiped on (for filtering or reference)
        swiped_experience_ids = [
            swipe.experience_id for swipe in 
            UserSwipe.query.filter_by(user_id=current_user_id).all()
        ]
        print(f"User {current_user_id}: Has already swiped on {len(swiped_experience_ids)} experiences")
        
        # Initialize experiences list
        all_experiences = []
        
        # Get all experiences except user's own
        query = Experience.query.filter(Experience.user_id != current_user_id)
        
        # Apply filtering for already swiped experiences if not including them
        if not include_swiped and swiped_experience_ids:
            query = query.filter(~Experience.id.in_(swiped_experience_ids))
            
        # Get all potential experiences
        all_experiences = query.all()
        print(f"User {current_user_id}: Found {len(all_experiences)} total experiences to rank")
        
        # If pinecone is initialized, use it to rank experiences by vector similarity
        if pinecone_initialized and hasattr(user, 'preference_vector') and user.preference_vector:
            print(f"User {current_user_id}: Ranking experiences using preference vector")
            
            # Create a list to hold experiences with their scores
            scored_experiences = []
            
            # Calculate vector similarity for each experience if possible
            for exp in all_experiences:
                # Check if experience is already swiped
                already_swiped = exp.id in swiped_experience_ids
                
                # Get the creator of the experience
                creator = User.query.get(exp.user_id)
                if not creator:
                    continue
                
                # If the experience has a vector, calculate similarity
                if hasattr(exp, 'vector') and exp.vector:
                    # Calculate similarity between user preference and experience vector
                    try:
                        user_vector = np.array(json.loads(user.preference_vector))
                        exp_vector = np.array(json.loads(exp.vector))
                        
                        # Calculate cosine similarity (or other similarity measure)
                        similarity = np.dot(user_vector, exp_vector) / (np.linalg.norm(user_vector) * np.linalg.norm(exp_vector))
                        
                        # For already swiped experiences, reduce the similarity slightly to prioritize new content
                        if already_swiped:
                            similarity *= 0.9  # Reduce score by 10% for already seen content
                        
                        # Add to scored experiences
                        scored_experiences.append({
                            'experience': exp,
                            'score': float(similarity),
                            'already_swiped': already_swiped,
                            'reason': get_match_reason(user, exp, {})
                        })
                    except (ValueError, TypeError, json.JSONDecodeError) as e:
                        print(f"Error calculating similarity for experience {exp.id}: {e}")
                        # If vector calculation fails, still include with neutral score
                        scored_experiences.append({
                            'experience': exp,
                            'score': 0.5,  # Neutral score
                            'already_swiped': already_swiped,
                            'reason': "New experience you might like"
                        })
                else:
                    # For experiences without vectors, assign a neutral score
                    scored_experiences.append({
                        'experience': exp,
                        'score': 0.5,  # Neutral score
                        'already_swiped': already_swiped,
                        'reason': "New experience you might like"
                    })
            
            # Sort experiences by score (highest first)
            scored_experiences.sort(key=lambda x: x['score'], reverse=True)
            
            # Log some information about the ranking
            print(f"User {current_user_id}: Ranked {len(scored_experiences)} experiences by preference similarity")
            
            # Prepare the final results
            experiences = [item['experience'] for item in scored_experiences]
            
            # Add match scores and reasons to the experiences
            for i, exp in enumerate(experiences):
                matching_item = next((item for item in scored_experiences if item['experience'].id == exp.id), None)
                if matching_item:
                    exp.match_score = matching_item['score']
                    exp.match_reason = matching_item['reason']
                    exp.already_swiped = matching_item['already_swiped']
        else:
            # If no vector ranking is possible, sort by recency
            print(f"User {current_user_id}: No preference vector available, sorting by recency")
            experiences = sorted(all_experiences, key=lambda x: x.created_at, reverse=True)
            
            # Add default scores and reasons
            for exp in experiences:
                exp.match_score = 0.5  # Default neutral score
                exp.match_reason = "Recent experience you might like"
                exp.already_swiped = exp.id in swiped_experience_ids
        
        print(f"User {current_user_id}: Preparing {len(experiences)} experiences for response")
        
        result = []
        for exp in experiences:
            # Get the creator of the experience
            creator = User.query.get(exp.user_id)
            
            # Skip if creator no longer exists (shouldn't happen but for safety)
            if not creator:
                print(f"User {current_user_id}: Skipping experience {exp.id} as creator no longer exists")
                continue
                
            # Clean up text data
            experience_type = exp.experience_type.strip() if exp.experience_type else ''
            location = exp.location.strip() if exp.location else ''
            description = exp.description.strip() if exp.description else ''
            
            # Check if this is a swiped experience for the 'already_swiped' flag
            already_swiped = hasattr(exp, 'already_swiped') and exp.already_swiped
            
            # Prepare result with match score and reason if available
            exp_data = {
                'id': exp.id,
                'user_id': exp.user_id,
                'creator_name': creator.name if creator else 'Unknown',
                'creator_netid': creator.netid if creator else '',
                'creator_profile_image': creator.profile_image if creator else None,
                'creator_class_year': creator.class_year if creator else None,  # Add class year for UI display
                'creator_major': creator.major if creator else None,  # Add major for UI display
                'experience_type': experience_type,
                'location': location,
                'description': description,
                'latitude': exp.latitude,
                'longitude': exp.longitude,
                'place_id': exp.place_id,
                'location_image': exp.location_image,
                'created_at': exp.created_at.isoformat() if exp.created_at else None,
                'already_swiped': already_swiped  # Flag to indicate if this has been swiped before
            }
            
            # Add match score and reason if available
            if hasattr(exp, 'match_score'):
                exp_data['match_score'] = float(exp.match_score)  # Convert to float to ensure it's JSON serializable
                exp_data['match_reason'] = getattr(exp, 'match_reason', "Experience you might like")
            
            result.append(exp_data)
        
        print(f"User {current_user_id}: Returning {len(result)} experiences for swiping")
        return jsonify(result)
    except Exception as e:
        print(f"User {current_user_id}: Error fetching swipe experiences: {e}")
        import traceback
        traceback.print_exc()  # Print stack trace for better debugging
        return jsonify({'detail': str(e)}), 500

def get_match_reason(user, experience, metadata):
    """Generate a human-readable reason why this experience might be a good match for the user"""
    
    reasons = []
    
    # Check for experience type match
    if user.experience_type_prefs and experience.experience_type:
        try:
            exp_prefs = json.loads(user.experience_type_prefs)
            if exp_prefs.get(experience.experience_type, False):
                reasons.append(f"You're interested in {experience.experience_type} experiences")
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Check for creator gender match
    creator = User.query.get(experience.user_id)
    if creator and user.gender_pref and creator.gender and creator.gender == user.gender_pref:
        reasons.append(f"Matches your gender preference: {creator.gender}")
    
    # Check for creator class year match
    if creator and creator.class_year and user.class_year_min_pref and user.class_year_max_pref:
        if user.class_year_min_pref <= creator.class_year <= user.class_year_max_pref:
            reasons.append(f"Creator is class of {creator.class_year}")
    
    # Check for similar interests
    if user.interests and creator and creator.interests:
        user_interests = user.interests.lower().split(',')
        creator_interests = creator.interests.lower().split(',')
        common_interests = [i.strip() for i in user_interests if any(i.strip() in c.strip() for c in creator_interests)]
        if common_interests:
            shared = common_interests[0] if len(common_interests) == 1 else "similar interests"
            reasons.append(f"You share {shared}")
    
    # If we have metadata from Pinecone with a high score
    if metadata.get('experience_type') == experience.experience_type:
        reasons.append(f"Based on your preferences for {experience.experience_type}")
    
    # Check swipe history patterns
    liked_swipes = UserSwipe.query.filter_by(user_id=user.id, direction=True).all()
    if liked_swipes:
        liked_experience_ids = [swipe.experience_id for swipe in liked_swipes]
        similar_liked = Experience.query.filter(
            Experience.id.in_(liked_experience_ids),
            Experience.experience_type == experience.experience_type
        ).first()
        if similar_liked:
            reasons.append(f"Similar to experiences you've liked")
    
    # If no specific reasons found, provide a generic one
    if not reasons:
        return "Experience you might enjoy based on your profile"
    
    # Return the top reason
    return reasons[0]

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
        
        # Step 1: Validate ticket with CAS server - Authentication happens first
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
        
        # Step 2: Check if user exists in our database - first by netid, then by cas_id
        user = User.query.filter_by(netid=netid).first()
        if not user:
            user = User.query.filter_by(cas_id=cas_id).first()
        
        is_new_user = False
        # If user doesn't exist, we'll create one with information from CAS
        if not user:
            is_new_user = True
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
                password_hash=secrets.token_hex(16),
                onboarding_completed=False,  # Explicitly set onboarding as not completed for new users
                phone_number=attributes.get('phoneNumber', ''),
                preferred_email=attributes.get('email', '')
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
        
        # Step 3: Determine if onboarding is needed
        # New users ALWAYS need onboarding, existing users only if onboarding_completed is False
        needs_onboarding = is_new_user or not user.onboarding_completed
        print(f"User {user.username} is new: {is_new_user}, needs onboarding: {needs_onboarding}")
        
        # Step 4: Redirect based on authentication and onboarding status
        # For production environment (Heroku) - CRITICAL FIX: Always redirect to root with hash params to avoid 404s
        if 'herokuapp.com' in request.host or os.environ.get('PRODUCTION') == 'true':
            # In SPAs on Heroku, we need to redirect to the root and let React Router handle it
            # Otherwise we get 404 errors when users don't have cookies
            print(f"Heroku environment detected, redirecting to root with appropriate hash")
            
            # Store auth tokens in secure HttpOnly cookies
            resp = None
            if needs_onboarding:
                # Send to root with #/onboarding hash for client-side routing
                resp = redirect(f"/?redirectTo=onboarding")
                print(f"Redirecting new user to onboarding")
            else:
                # For authenticated users with completed onboarding
                target = callback_url.lstrip('/') if callback_url != '/' else 'swipe'
                resp = redirect(f"/?redirectTo={target}")
                print(f"Redirecting authenticated user to {target}")
            
            # Set tokens in cookies for good measure
            resp.set_cookie('access_token', access_token, httponly=True, secure=True, max_age=86400)
            resp.set_cookie('refresh_token', refresh_token, httponly=True, secure=True, max_age=2592000)
            return resp
        
        # For local development - redirect directly to the route
        else:
            if needs_onboarding:
                print(f"Local dev: Redirecting to {frontend_url}/onboarding")
                return redirect(f"{frontend_url}/onboarding")
            else:
                target = f"{frontend_url}/{callback_url.lstrip('/')}" if callback_url != '/' else f"{frontend_url}/swipe"
                print(f"Local dev: Redirecting to {target}")
                return redirect(target)
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
            if 'class_year_min_pref' in data:
                # Validate class year is within reasonable bounds
                try:
                    if data['class_year_min_pref'] is not None:
                        year_val = int(data['class_year_min_pref'])
                        if year_val < 2000 or year_val > 2100:
                            return jsonify({'detail': 'Class year must be between 2000 and 2100'}), 400
                    user.class_year_min_pref = data['class_year_min_pref']
                    preference_fields_updated = True
                except (ValueError, TypeError):
                    return jsonify({'detail': 'Invalid class year value'}), 400
            if 'class_year_max_pref' in data:
                # Validate class year is within reasonable bounds
                try:
                    if data['class_year_max_pref'] is not None:
                        year_val = int(data['class_year_max_pref'])
                        if year_val < 2000 or year_val > 2100:
                            return jsonify({'detail': 'Class year must be between 2000 and 2100'}), 400
                    user.class_year_max_pref = data['class_year_max_pref']
                    preference_fields_updated = True
                except (ValueError, TypeError):
                    return jsonify({'detail': 'Invalid class year value'}), 400
            if 'interests_prefs' in data:
                user.interests_prefs = data['interests_prefs']
                preference_fields_updated = True
            # Add handling for phone_number and preferred_email fields
            if 'phone_number' in data:
                user.phone_number = data['phone_number']
            if 'preferred_email' in data:
                user.preferred_email = data['preferred_email']
            
            # If preferences were updated, invalidate the cached preference vector
            if preference_fields_updated:
                print(f"User {user.id}: Preferences updated, invalidating cached preference vector")
                user.preference_vector = None
                user.preference_vector_updated_at = None
            
            # Save all changes to the database
            db.session.commit()
            
            # Log if preference fields were updated for visibility
            if preference_fields_updated:
                print(f"User {user.id} updated their preferences. Personalized recommendations will be refreshed.")
                
                # Pre-warm the personalized recommendations by querying Pinecone
                if pinecone_initialized:
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

# Profile Image Management API Endpoints
@app.route('/api/users/images', methods=['POST'])
@login_required()
def upload_user_image(current_user_id=None):
    """
    Upload a user profile image to Cloudinary and save the URL to the database.
    Users can have up to 4 images. If a user already has 4 images, the oldest one will be replaced.
    """
    try:
        # Check if the request contains a file
        if 'image' not in request.files:
            return jsonify({'detail': 'No image file provided'}), 400
            
        image_file = request.files['image']
        
        # Check if the file is valid
        if image_file.filename == '':
            return jsonify({'detail': 'No image file selected'}), 400
            
        # Check if the content type is an image
        if not image_file.content_type.startswith('image/'):
            return jsonify({'detail': 'File must be an image'}), 400
            
        # Get user's existing images
        user_images = UserImage.query.filter_by(user_id=current_user_id).order_by(UserImage.created_at).all()
        
        # Calculate position for the new image
        position = request.form.get('position')
        if position is not None:
            try:
                position = int(position)
                if position < 0 or position > 3:
                    return jsonify({'detail': 'Position must be between 0 and 3'}), 400
            except ValueError:
                return jsonify({'detail': 'Position must be a number between 0 and 3'}), 400
        else:
            # If no position provided, use the next available position
            existing_positions = [img.position for img in user_images]
            for pos in range(4):  # Try positions 0-3
                if pos not in existing_positions:
                    position = pos
                    break
            else:
                # If all positions are taken, replace the oldest image
                position = user_images[0].position
                # Delete the oldest image
                old_image = user_images[0]
                
                # Delete from Cloudinary
                try:
                    cloudinary.uploader.destroy(old_image.public_id)
                except Exception as e:
                    print(f"Error deleting image from Cloudinary: {e}")
                
                # Delete from database
                db.session.delete(old_image)
                db.session.commit()
        
        # Upload the file to Cloudinary
        upload_result = cloudinary.uploader.upload(
            image_file,
            folder=f"dateabase/users/{current_user_id}",
            public_id=f"profile_{position}_{datetime.utcnow().timestamp()}"
        )
        
        # Create a new UserImage
        new_image = UserImage(
            user_id=current_user_id,
            image_url=upload_result['secure_url'],
            public_id=upload_result['public_id'],
            position=position
        )
        
        # If this is the first image or position is 0, also set it as the user's primary profile image
        if position == 0 or len(user_images) == 0:
            user = User.query.get(current_user_id)
            user.profile_image = upload_result['secure_url']
        
        db.session.add(new_image)
        db.session.commit()
        
        return jsonify({
            'message': 'Image uploaded successfully',
            'image': {
                'id': new_image.id,
                'url': new_image.image_url,
                'position': new_image.position,
                'created_at': new_image.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        print(f"Error uploading image: {e}")
        db.session.rollback()
        return jsonify({'detail': str(e)}), 500
        
@app.route('/api/users/images', methods=['GET'])
@login_required()
def get_user_images(current_user_id=None):
    """Get all images for the current user."""
    try:
        user_images = UserImage.query.filter_by(user_id=current_user_id).order_by(UserImage.position).all()
        
        images = []
        for img in user_images:
            images.append({
                'id': img.id,
                'url': img.image_url,
                'position': img.position,
                'created_at': img.created_at.isoformat()
            })
            
        return jsonify(images)
    except Exception as e:
        print(f"Error getting user images: {e}")
        return jsonify({'detail': str(e)}), 500
        
@app.route('/api/users/images/<int:image_id>', methods=['DELETE'])
@login_required()
def delete_user_image(image_id, current_user_id=None):
    """Delete a user image."""
    try:
        # Get the image
        image = UserImage.query.get(image_id)
        if not image:
            return jsonify({'detail': 'Image not found'}), 404
            
        # Check if the user owns the image
        if image.user_id != current_user_id:
            return jsonify({'detail': 'You can only delete your own images'}), 403
            
        # Delete from Cloudinary
        try:
            cloudinary.uploader.destroy(image.public_id)
        except Exception as e:
            print(f"Error deleting image from Cloudinary: {e}")
            
        # If this is the primary profile image, clear it
        user = User.query.get(current_user_id)
        if user.profile_image == image.image_url:
            # Find another image to use as the profile image
            other_image = UserImage.query.filter(
                UserImage.user_id == current_user_id,
                UserImage.id != image_id
            ).first()
            
            if other_image:
                user.profile_image = other_image.image_url
            else:
                user.profile_image = None
        
        # Delete from database
        db.session.delete(image)
        db.session.commit()
        
        return jsonify({'message': 'Image deleted successfully'}), 200
    except Exception as e:
        print(f"Error deleting image: {e}")
        db.session.rollback()
        return jsonify({'detail': str(e)}), 500

@app.route('/api/users/images/<int:image_id>/set-position', methods=['PUT'])
@login_required()
def update_image_position(image_id, current_user_id=None):
    """Update the position of a user image."""
    try:
        # Get the position from the request
        data = request.json
        if 'position' not in data:
            return jsonify({'detail': 'Position is required'}), 400
            
        position = data['position']
        if not isinstance(position, int) or position < 0 or position > 3:
            return jsonify({'detail': 'Position must be a number between 0 and 3'}), 400
            
        # Get the image
        image = UserImage.query.get(image_id)
        if not image:
            return jsonify({'detail': 'Image not found'}), 404
            
        # Check if the user owns the image
        if image.user_id != current_user_id:
            return jsonify({'detail': 'You can only update your own images'}), 403
            
        # If there's already an image at the requested position, swap positions
        existing_image = UserImage.query.filter(
            UserImage.user_id == current_user_id,
            UserImage.position == position,
            UserImage.id != image_id
        ).first()
        
        if existing_image:
            existing_image.position = image.position
            
        # Update the position
        image.position = position
        
        # If this is position 0, also set it as the primary profile image
        if position == 0:
            user = User.query.get(current_user_id)
            user.profile_image = image.image_url
            
        db.session.commit()
        
        return jsonify({
            'message': 'Image position updated',
            'image': {
                'id': image.id,
                'url': image.image_url,
                'position': image.position
            }
        })
    except Exception as e:
        print(f"Error updating image position: {e}")
        db.session.rollback()
        return jsonify({'detail': str(e)}), 500

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