#!/usr/bin/env python3
import os
import sys
from sqlalchemy import create_engine

def reset_match_tables():
    # Get the database URL from environment variables
    database_url = os.environ.get('DATABASE_URL')
    
    # Convert postgres:// to postgresql:// if needed
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    if not database_url:
        print("Error: DATABASE_URL environment variable not found.")
        print("Make sure you run this script on Heroku with: heroku run python backend/reset_matches.py")
        sys.exit(1)
    
    print("Connecting to database...")
    
    try:
        # Create SQLAlchemy engine
        engine = create_engine(database_url)
        connection = engine.connect()
        
        print("Successfully connected to database.")
        
        # Truncate the match and user_swipe tables
        print("Truncating Match and UserSwipe tables...")
        
        # Execute truncate commands
        connection.execute('TRUNCATE TABLE "match" CASCADE;')
        connection.execute('TRUNCATE TABLE "user_swipe" CASCADE;')
        
        # Verify the tables are empty
        match_count = connection.execute('SELECT COUNT(*) FROM "match";').scalar()
        swipe_count = connection.execute('SELECT COUNT(*) FROM "user_swipe";').scalar()
        
        print(f"Verification: Match table has {match_count} rows")
        print(f"Verification: UserSwipe table has {swipe_count} rows")
        
        # Close the connection
        connection.close()
        
        print("Reset complete. All matches and swipes have been cleared.")
        print("Users can now start fresh with new swipes.")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("===== Match and UserSwipe Table Reset Tool =====")
    print("This script will delete ALL matches and swipes in the database.")
    print("It will NOT affect users, experiences, or any other data.")
    
    confirmation = input("Are you sure you want to proceed? (y/n): ")
    
    if confirmation.lower() == 'y':
        reset_match_tables()
    else:
        print("Operation cancelled.") 