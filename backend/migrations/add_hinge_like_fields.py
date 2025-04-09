"""
Migration script to add Hinge-like fields to User table
"""
import sys
import os

# Add parent directory to path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules from the Flask application
from app import app, db
from sqlalchemy import text

def run_migration():
    """Add Hinge-like fields to User table"""
    try:
        with app.app_context():
            # Check if we're using SQLite or PostgreSQL
            dialect = db.engine.dialect.name
            
            print(f"Using {dialect} database")
            
            with db.engine.connect() as connection:
                # Add new columns
                if dialect == "sqlite":
                    # For SQLite, use ALTER TABLE
                    print("Adding new columns to User table in SQLite...")
                    connection.execute(text('ALTER TABLE user ADD COLUMN sexuality VARCHAR(30)'))
                    connection.execute(text('ALTER TABLE user ADD COLUMN height INTEGER'))
                    connection.execute(text('ALTER TABLE user ADD COLUMN location VARCHAR(100)'))
                    connection.execute(text('ALTER TABLE user ADD COLUMN hometown VARCHAR(100)'))
                    connection.execute(text('ALTER TABLE user ADD COLUMN major VARCHAR(100)'))
                    connection.execute(text('ALTER TABLE user ADD COLUMN prompt1 VARCHAR(200)'))
                    connection.execute(text('ALTER TABLE user ADD COLUMN answer1 TEXT'))
                    connection.execute(text('ALTER TABLE user ADD COLUMN prompt2 VARCHAR(200)'))
                    connection.execute(text('ALTER TABLE user ADD COLUMN answer2 TEXT'))
                    connection.execute(text('ALTER TABLE user ADD COLUMN prompt3 VARCHAR(200)'))
                    connection.execute(text('ALTER TABLE user ADD COLUMN answer3 TEXT'))
                    connection.commit()
                
                elif dialect == "postgresql":
                    # For PostgreSQL, use ALTER TABLE with IF NOT EXISTS
                    print("Adding new columns to User table in PostgreSQL...")
                    connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS sexuality VARCHAR(30)'))
                    connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS height INTEGER'))
                    connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS location VARCHAR(100)'))
                    connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS hometown VARCHAR(100)'))
                    connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS major VARCHAR(100)'))
                    connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS prompt1 VARCHAR(200)'))
                    connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS answer1 TEXT'))
                    connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS prompt2 VARCHAR(200)'))
                    connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS answer2 TEXT'))
                    connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS prompt3 VARCHAR(200)'))
                    connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS answer3 TEXT'))
                    connection.commit()
                
                else:
                    print(f"Unsupported database dialect: {dialect}")
                    return False
                
                print("Migration completed successfully!")
                return True
                
    except Exception as e:
        print(f"Error during migration: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1) 