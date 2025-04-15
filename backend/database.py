from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
import os

# Initialize SQLAlchemy without an app (we'll configure it later)
db = SQLAlchemy()

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # Increased from 128 to 255
    cas_id = db.Column(db.String(50), unique=True, nullable=True)  # CAS unique identifier
    netid = db.Column(db.String(50), unique=True, nullable=True)  # Princeton NetID
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(20), nullable=True)  # Made nullable for initial CAS login
    sexuality = db.Column(db.String(30), nullable=True)  # Added for Hinge-like onboarding
    height = db.Column(db.Integer, nullable=True)  # Height in cm
    location = db.Column(db.String(100), nullable=True)  # Location/area
    hometown = db.Column(db.String(100), nullable=True)  # Hometown
    major = db.Column(db.String(100), nullable=True)  # Major
    class_year = db.Column(db.Integer, nullable=True)  # Made nullable for initial CAS login
    interests = db.Column(db.Text, nullable=True)  # Made nullable for initial CAS login
    profile_image = db.Column(db.Text, nullable=True)  # URL to profile image
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    onboarding_completed = db.Column(db.Boolean, default=False)  # Track if user has completed onboarding
    # Hinge-like prompt responses
    prompt1 = db.Column(db.String(200), nullable=True)  # The prompt question
    answer1 = db.Column(db.Text, nullable=True)  # The answer to prompt 1
    prompt2 = db.Column(db.String(200), nullable=True)  # The prompt question
    answer2 = db.Column(db.Text, nullable=True)  # The answer to prompt 2
    prompt3 = db.Column(db.String(200), nullable=True)  # The prompt question
    answer3 = db.Column(db.Text, nullable=True)  # The answer to prompt 3
    
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
    tags = db.Column(db.Text, nullable=True)  # Store tags as JSON string
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

def add_onboarding_column(app):
    """Add onboarding_completed column to User table if it doesn't exist"""
    print("Starting migration to add onboarding_completed column...")
    with app.app_context():
        # Check if we're using SQLite or PostgreSQL
        dialect = db.engine.dialect.name
        print(f"Using {dialect} database")
        
        try:
            with db.engine.connect() as connection:
                if dialect == "sqlite":
                    # For SQLite
                    connection.execute(text('ALTER TABLE user ADD COLUMN onboarding_completed BOOLEAN DEFAULT 0'))
                    connection.commit()
                elif dialect == "postgresql":
                    # For PostgreSQL
                    connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE'))
                    connection.commit()
                else:
                    print(f"Unsupported database dialect: {dialect}")
                    return False
                
                print("Column added successfully!")
                return True
        except Exception as e:
            print(f"Error: {e}")
            if "duplicate column name" in str(e):
                print("Column already exists. This is fine.")
                return True
            return False

# Function to initialize the database with the Flask app
def init_db(app):
    # Database configuration
    db_url = os.environ.get('DATABASE_URL', 'postgresql://ueaqcj622ro270:pf6999e838eb1f1f2e5af5b4b9d17b2fcdc2475e46597ea2d0dcdbd6bdb1e13af@ceqbglof0h8enj.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dc26u3dpl6nepd')
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
