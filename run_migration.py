import os
import sys
import importlib
from backend.migrations.add_experience_name_field import add_experience_name_field
from flask import Flask
from backend.database import db

def run_migration():
    """Run the database migration to add experience_name field to Experience table"""
    try:
        # Create a Flask app instance
        app = Flask(__name__)
        
        # Configure the database
        DATABASE_URL = os.environ.get('DATABASE_URL', '')
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        
        app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///backend/app.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize the database with the app
        db.init_app(app)
        
        # Run the migration
        success = add_experience_name_field(app)
        
        if success:
            print("Migration completed! Experience name field added successfully.")
            return True
        else:
            print("Migration failed!")
            return False
            
    except Exception as e:
        print(f"Error during migration: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("Migration completed successfully.")
    else:
        print("Migration failed. Check the logs for details.") 