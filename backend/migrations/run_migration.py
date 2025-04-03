"""
Run database migration to add onboarding_completed column to User table
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules from the Flask application
from app import app, db
from sqlalchemy import Column, Boolean, text

def run_migration():
    """Add onboarding_completed column to User table if it doesn't exist"""
    try:
        with app.app_context():
            # Check if we're using SQLite or PostgreSQL
            dialect = db.engine.dialect.name
            
            print(f"Using {dialect} database")
            
            if dialect == "sqlite":
                # For SQLite, use ALTER TABLE
                # First check if column exists
                inspector = db.inspect(db.engine)
                columns = [col['name'] for col in inspector.get_columns('user')]
                
                if 'onboarding_completed' not in columns:
                    print("Adding 'onboarding_completed' column to User table...")
                    with db.engine.connect() as connection:
                        connection.execute(text('ALTER TABLE user ADD COLUMN onboarding_completed BOOLEAN DEFAULT 0'))
                        connection.commit()
                    print("Column added successfully!")
                else:
                    print("Column 'onboarding_completed' already exists.")
            
            elif dialect == "postgresql":
                # For PostgreSQL, use ALTER TABLE with IF NOT EXISTS
                print("Adding 'onboarding_completed' column to User table (if not exists)...")
                with db.engine.connect() as connection:
                    connection.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE'))
                    connection.commit()
                print("Migration completed for PostgreSQL!")
            
            else:
                print(f"Unsupported database dialect: {dialect}")
                return False
                
            return True
                
    except Exception as e:
        print(f"Error during migration: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
