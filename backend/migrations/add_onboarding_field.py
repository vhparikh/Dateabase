"""
Migration script to add onboarding_completed field to User table
"""
import sqlite3
import os
import sys

# Add parent directory to path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_migration():
    """Add onboarding_completed column to User table if it doesn't exist"""
    try:
        # Get database path from environment or use default
        db_url = os.environ.get('DATABASE_URL', 'sqlite:///dateabase.db')
        
        # For SQLite database
        if db_url.startswith('sqlite:///'):
            db_path = db_url.replace('sqlite:///', '')
            # Handle relative path
            if not os.path.isabs(db_path):
                db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), db_path)
            
            print(f"Using SQLite database at: {db_path}")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables first to find the user table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [table[0] for table in cursor.fetchall()]
            print(f"Available tables: {tables}")
            
            # The table could be named 'user' or 'users' - check both
            table_name = None
            if 'user' in tables:
                table_name = 'user'
            elif 'users' in tables:
                table_name = 'users'
                
            if not table_name:
                print("Error: Could not find user table!")
                return False
                
            # Check if column exists
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [column[1] for column in cursor.fetchall()]
            print(f"Existing columns: {columns}")
            
            if 'onboarding_completed' not in columns:
                print(f"Adding 'onboarding_completed' column to {table_name} table...")
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN onboarding_completed BOOLEAN DEFAULT 0")
                conn.commit()
                print("Column added successfully!")
            else:
                print("Column 'onboarding_completed' already exists.")
            
            conn.close()
        else:
            # For PostgreSQL (on Heroku)
            print("This migration script only supports SQLite. For PostgreSQL, use database migration tools like Alembic.")
            return False
            
        return True
    except Exception as e:
        print(f"Error during migration: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
