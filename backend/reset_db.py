import os
import sys
from flask import Flask
from sqlalchemy import text

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # Import database components
    from backend.database import db, init_db, Experience, User, Match, UserSwipe, UserImage
except ImportError:
    # Fall back to direct import for local development
    from database import db, init_db, Experience, User, Match, UserSwipe, UserImage

# Create a Flask app
app = Flask(__name__)

def reset_database():
    """Reset the database by dropping all tables and recreating them"""
    print("Starting database reset process...")
    
    # Initialize the database with our app
    init_db(app)
    
    with app.app_context():
        try:
            # Check if we're using SQLite or PostgreSQL
            dialect = db.engine.dialect.name
            print(f"Using {dialect} database")
            
            # Get all table names
            tables = db.inspect(db.engine).get_table_names()
            print(f"Existing tables: {tables}")
            
            # Drop all tables
            print("Dropping all tables...")
            db.drop_all()
            print("All tables dropped successfully")
            
            # If using PostgreSQL, attempt to modify the Experience table
            if dialect == "postgresql":
                try:
                    # Adding experience_name column to the Experience model if it doesn't exist
                    with db.engine.connect() as connection:
                        print("Creating tables...")
                        db.create_all()
                        print("Tables created")
                        
                        # Ensure experience_name column exists in Experience table
                        print("Ensuring experience_name column exists...")
                        connection.execute(text('ALTER TABLE experience ADD COLUMN IF NOT EXISTS experience_name VARCHAR(200)'))
                        connection.commit()
                        print("experience_name column added or confirmed")
                except Exception as e:
                    print(f"Error ensuring experience_name column: {e}")
            else:
                # For SQLite or other databases, just recreate tables
                print("Creating tables...")
                db.create_all()
                print("Tables created")
            
            # Verify Experience table schema
            inspector = db.inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('experience')]
            print(f"Experience table columns: {columns}")
            
            if 'experience_name' not in columns:
                print("WARNING: experience_name column is missing from the Experience table!")
            else:
                print("Confirmed: experience_name column exists in Experience table")
                
            print("Database reset completed successfully!")
            return True
            
        except Exception as e:
            print(f"Error resetting database: {e}")
            return False

if __name__ == "__main__":
    reset_database() 