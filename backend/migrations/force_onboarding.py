"""
Migration script to force onboarding_completed field to False for all users
"""
import sys
import os

# Add parent directory to path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules from the Flask application
from app import app, db
from database import User
from sqlalchemy import text

def run_migration():
    """Force onboarding_completed to False for all users"""
    try:
        with app.app_context():
            # Check if we're using SQLite or PostgreSQL
            dialect = db.engine.dialect.name
            
            print(f"Using {dialect} database")
            
            # Update all users to set onboarding_completed to False
            user_count = User.query.count()
            print(f"Found {user_count} users in the database")
            
            # Update ALL users to False regardless of current value
            users = User.query.all()
            updated_count = 0
            
            for user in users:
                # Set to False for ALL users, not just where it was True before
                user.onboarding_completed = False
                updated_count += 1
            
            db.session.commit()
            print(f"Successfully forced onboarding status to False for {updated_count} users")
            
            return True
                
    except Exception as e:
        print(f"Error during migration: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1) 