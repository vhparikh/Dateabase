from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import os
import sys

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from parent directory
from database import db, init_db

def add_preference_fields(app):
    """Add preference fields to User table"""
    print("Starting migration to add preference fields...")
    with app.app_context():
        # Check if we're using SQLite or PostgreSQL
        dialect = db.engine.dialect.name
        print(f"Using {dialect} database")
        
        try:
            with db.engine.connect() as connection:
                if dialect == "sqlite":
                    # For SQLite
                    connection.execute(text('ALTER TABLE user ADD COLUMN gender_pref TEXT'))
                    connection.execute(text('ALTER TABLE user ADD COLUMN experience_type_prefs TEXT'))
                    connection.execute(text('ALTER TABLE user ADD COLUMN class_year_min_pref INTEGER'))
                    connection.execute(text('ALTER TABLE user ADD COLUMN class_year_max_pref INTEGER'))
                    connection.execute(text('ALTER TABLE user ADD COLUMN interests_prefs TEXT'))
                    connection.commit()
                elif dialect == "postgresql":
                    # For PostgreSQL
                    connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS gender_pref TEXT'))
                    connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS experience_type_prefs TEXT'))
                    connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS class_year_min_pref INTEGER'))
                    connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS class_year_max_pref INTEGER'))
                    connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS interests_prefs TEXT'))
                    connection.commit()
                else:
                    print(f"Unsupported database dialect: {dialect}")
                    return False
                
                print("Preference columns added successfully!")
                return True
        except Exception as e:
            print(f"Error: {e}")
            if "duplicate column name" in str(e):
                print("One or more columns already exist. This is fine.")
                return True
            return False

if __name__ == "__main__":
    # Create a minimal Flask app
    app = Flask(__name__)
    
    # Init the app with SQLAlchemy
    init_db(app)
    
    # Run the migration
    success = add_preference_fields(app)
    
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!") 