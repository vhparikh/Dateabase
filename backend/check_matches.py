#!/usr/bin/env python3
import os
import sys
from sqlalchemy import create_engine, text

def check_match_tables():
    """
    Check the Match and UserSwipe tables to verify data is being created correctly.
    Prints the current state of the tables and recent entries.
    """
    # Get the database URL from environment variables
    database_url = os.environ.get('DATABASE_URL')
    
    # Convert postgres:// to postgresql:// if needed
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    if not database_url:
        print("Error: DATABASE_URL environment variable not found.")
        print("Make sure you run this script on Heroku with: heroku run python backend/check_matches.py")
        sys.exit(1)
    
    print("Connecting to database to check match tables...")
    
    try:
        # Create SQLAlchemy engine
        engine = create_engine(database_url)
        connection = engine.connect()
        
        print("Successfully connected to database.")
        
        # Check counts in both tables
        swipes_count = connection.execute(text('SELECT COUNT(*) FROM "user_swipe";')).scalar()
        matches_count = connection.execute(text('SELECT COUNT(*) FROM "match";')).scalar()
        
        print(f"Status: UserSwipe table has {swipes_count} records")
        print(f"Status: Match table has {matches_count} records")
        
        # Show the 5 most recent swipes
        print("\nMost recent swipes:")
        recent_swipes = connection.execute(text('''
            SELECT us.id, us.user_id, u.name as user_name, 
                   us.experience_id, e.experience_type, 
                   us.direction, us.created_at
            FROM "user_swipe" us
            JOIN "user" u ON us.user_id = u.id
            JOIN "experience" e ON us.experience_id = e.id
            ORDER BY us.created_at DESC
            LIMIT 5;
        ''')).fetchall()
        
        for swipe in recent_swipes:
            print(f"Swipe ID: {swipe[0]}, User: {swipe[1]} ({swipe[2]}), " +
                  f"Experience: {swipe[3]} ({swipe[4]}), " +
                  f"Direction: {'Like' if swipe[5] else 'Pass'}, " +
                  f"Created: {swipe[6]}")
        
        # Show the 5 most recent matches
        print("\nMost recent matches:")
        recent_matches = connection.execute(text('''
            SELECT m.id, m.user1_id, u1.name as user1_name, 
                   m.user2_id, u2.name as user2_name,
                   m.experience_id, e.experience_type, 
                   m.status, m.created_at
            FROM "match" m
            JOIN "user" u1 ON m.user1_id = u1.id
            JOIN "user" u2 ON m.user2_id = u2.id
            JOIN "experience" e ON m.experience_id = e.id
            ORDER BY m.created_at DESC
            LIMIT 5;
        ''')).fetchall()
        
        for match in recent_matches:
            print(f"Match ID: {match[0]}, " +
                  f"User1: {match[1]} ({match[2]}), " +
                  f"User2: {match[3]} ({match[4]}), " +
                  f"Experience: {match[5]} ({match[6]}), " +
                  f"Status: {match[7]}, " +
                  f"Created: {match[8]}")
        
        # Close the connection
        connection.close()
        
    except Exception as e:
        print(f"Error checking match tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("===== Match Tables Diagnostic Tool =====")
    check_match_tables()
    print("\nDiagnostic complete. If matches are being created correctly,")
    print("you should see recent entries in both tables.")
    print("If you're not seeing matches display in the UI, check the frontend code.") 