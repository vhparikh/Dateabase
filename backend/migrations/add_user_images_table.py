import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory to the path so we can import from the backend package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from database import db
except ImportError:
    print("Error: Unable to import db from database.py")
    sys.exit(1)

def run_migration():
    """Add UserImage table to the database"""
    try:
        from flask import Flask
        
        # Create a Flask app context for the migration
        app = Flask(__name__)
        
        # Get database URL from environment or use default for development
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if DATABASE_URL:
            # Heroku prepends "postgres://" but SQLAlchemy expects "postgresql://"
            if DATABASE_URL.startswith('postgres://'):
                DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
            app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
        else:
            # Default SQLite database for development
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dateabase.db'
        
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)
        
        with app.app_context():
            # Connect to the database
            engine = db.engine
            connection = engine.connect()
            
            # Detect the database type
            dialect = engine.dialect.name
            
            print(f"Connected to database: {dialect}")
            
            if dialect == "sqlite":
                # For SQLite, use SQLite syntax
                print("Adding UserImage table to SQLite database...")
                connection.execute(text('''
                CREATE TABLE IF NOT EXISTS user_image (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    image_url TEXT NOT NULL,
                    public_id VARCHAR(255) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    position INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
                '''))
                connection.commit()
                
            elif dialect == "postgresql":
                # For PostgreSQL, use PostgreSQL syntax
                print("Adding UserImage table to PostgreSQL database...")
                connection.execute(text('''
                CREATE TABLE IF NOT EXISTS user_image (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    image_url TEXT NOT NULL,
                    public_id VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    position INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES "user" (id)
                )
                '''))
                connection.commit()
                
            else:
                print(f"Unsupported database dialect: {dialect}")
                return False
            
            print("Migration completed successfully!")
            return True
                
    except Exception as e:
        print(f"Error during migration: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("UserImage table added successfully.")
    else:
        print("Failed to add UserImage table.")
        sys.exit(1) 