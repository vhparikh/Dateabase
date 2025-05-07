from flask import Flask, request, jsonify, send_from_directory, redirect, session, url_for
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect, generate_csrf
from datetime import datetime, timedelta, timezone
import os
import secrets
import google.generativeai as genai
import cloudinary
import cloudinary.uploader
import cloudinary.api
from urllib.parse import quote_plus, urlencode, quote
import pinecone
import json
import cohere  # Import Cohere client
from sqlalchemy import text
from functools import wraps

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
from .routes.gemini_routes import gemini_bp
from .routes.help_routes import help_bp, help_frontend_bp

# Create the app first before registering blueprints
app = Flask(__name__, static_folder='../frontend/build', static_url_path='')
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})

# Enable CSRF protection for the Flask app
csrf = CSRFProtect(app)

# Now register the blueprint after app is defined
app.register_blueprint(fix_images_bp)
app.register_blueprint(experience_bp)
app.register_blueprint(swipe_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(match_bp)
app.register_blueprint(image_bp)
app.register_blueprint(user_bp)
app.register_blueprint(gemini_bp)
app.register_blueprint(help_bp)
app.register_blueprint(help_frontend_bp)
from .database import db, init_db, User, Experience, Match, UserSwipe, UserImage

# Setup Flask app with proper static folder configuration for production deployment
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')
# Set session type for CAS auth
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Initialize the database with our app
init_db(app)

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

# CSRF token endpoint to provide tokens to the frontend
@csrf.exempt
@app.route('/api/csrf-token', methods=['GET'])
def get_csrf_token():
    token = generate_csrf()
    response = jsonify({'csrf_token': token})
    return response

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