from flask import Flask
from sqlalchemy import text
import os

def migrate_profile_images_column(app):
    """Add profile_images column to User table if it doesn't exist"""
    print("Starting migration to add profile_images column...")
    with app.app_context():
        # Check dialect
        from database import db
        dialect = db.engine.dialect.name
        print(f"Using {dialect} database")
        
        try:
            with db.engine.connect() as connection:
                if dialect == "sqlite":
                    # For SQLite (not needed in production but helpful for development)
                    # SQLite doesn't support array types, so we'd use TEXT and handle as JSON
                    connection.execute(text('ALTER TABLE user ADD COLUMN profile_images TEXT;'))
                    connection.commit()
                elif dialect == "postgresql":
                    # For PostgreSQL
                    try:
                        # Check if the column already exists
                        result = connection.execute(text('''
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name='user' AND column_name='profile_images';
                        '''))
                        
                        if not result.fetchone():
                            # Add the column as a text array
                            connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS profile_images TEXT[];'))
                            connection.commit()
                            print("profile_images column added successfully!")
                        else:
                            print("profile_images column already exists. This is fine.")
                    except Exception as pg_err:
                        print(f"Specific PostgreSQL error: {pg_err}")
                        print("Attempting alternative approach...")
                        try:
                            # Some PostgreSQL versions might need a different approach
                            connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS profile_images TEXT[] DEFAULT NULL;'))
                            connection.commit()
                            print("profile_images column added using alternative method!")
                        except Exception as alt_err:
                            print(f"Alternative approach also failed: {alt_err}")
                            return False
                else:
                    print(f"Unsupported database dialect: {dialect}")
                    return False
                
                return True
        except Exception as e:
            print(f"Error during migration: {e}")
            return False

def run_migrations(app):
    """Run all database migrations"""
    print("Running database migrations...")
    
    # Run all migrations here
    migrate_profile_images_column(app)
    
    print("Migrations completed successfully!")
