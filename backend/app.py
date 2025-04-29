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
from .routes.user_routes import user_bp

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
app.register_blueprint(user_bp)

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