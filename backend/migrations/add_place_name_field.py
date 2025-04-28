from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import os
import sys

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from parent directory
from database import db, init_db

def add_place_name_field(app):
    """Add place_name field to Experience table"""
    print("Starting migration to add place_name field to Experience table...")
    with app.app_context():
        # Check if we're using SQLite or PostgreSQL
        dialect = db.engine.dialect.name
        print(f"Using {dialect} database")
        
        try:
            with db.engine.connect() as connection:
                if dialect == "sqlite":
                    # For SQLite
                    connection.execute(text('ALTER TABLE experience ADD COLUMN place_name TEXT'))
                    connection.commit()
                elif dialect == "postgresql":
                    # For PostgreSQL
                    connection.execute(text('ALTER TABLE experience ADD COLUMN IF NOT EXISTS place_name TEXT'))
                    connection.commit()
                
                print("Migration completed successfully.")
        except Exception as e:
            print(f"Error during migration: {e}")
            return False
    
    return True

if __name__ == "__main__":
    # Create a Flask app instance
    app = Flask(__name__)
    
    # Configure the database
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database with the app
    db.init_app(app)
    
    # Run the migration
    success = add_place_name_field(app)
    if success:
        print("Place name field added successfully to Experience table.")
    else:
        print("Failed to add place name field to Experience table.") 