from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Initialize SQLAlchemy without an app (we'll configure it later)
db = SQLAlchemy()

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

# Function to initialize the database with the Flask app
def init_db(app):
    # Database configuration
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///dateabase.db')
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the app with SQLAlchemy
    db.init_app(app)
    
    # Create tables within app context if they don't exist
    with app.app_context():
        db.create_all()

    return db
