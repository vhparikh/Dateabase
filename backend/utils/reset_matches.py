#!/usr/bin/env python3
"""
Reset script for Dateabase application.
This script clears all records from the Match and UserSwipe tables.
"""

import os
import sys
from flask import Flask
import argparse

# Add the backend directory to the path to allow importing database models
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from backend.database import db, Match, UserSwipe

def reset_matches_and_swipes(confirm=False):
    """
    Delete all records from Match and UserSwipe tables
    
    Args:
        confirm (bool): Whether to require confirmation before deletion
    
    Returns:
        bool: Success status
    """
    if not confirm:
        confirmation = input("This will delete ALL matches and swipes. Are you sure? (y/n): ").strip().lower()
        if confirmation != 'y':
            print("Operation cancelled.")
            return False
    
    app = Flask(__name__)
    
    # Get database URL from environment or use default for development
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://ueaqcj622ro270:pf6999e838eb1f1f2e5af5b4b9d17b2fcdc2475e46597ea2d0dcdbd6bdb1e13af@ceqbglof0h8enj.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dc26u3dpl6nepd')
    
    # Heroku prepends "postgres://" but SQLAlchemy expects "postgresql://"
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the app with SQLAlchemy
    db.init_app(app)
    
    with app.app_context():
        try:
            # Count existing records before deletion
            match_count = Match.query.count()
            swipe_count = UserSwipe.query.count()
            
            # Delete all records from Match table
            Match.query.delete()
            
            # Delete all records from UserSwipe table
            UserSwipe.query.delete()
            
            # Commit changes
            db.session.commit()
            
            print(f"Successfully deleted {match_count} matches and {swipe_count} swipes.")
            print("Match and UserSwipe tables have been reset successfully.")
            return True
        
        except Exception as e:
            print(f"Error resetting database tables: {e}")
            db.session.rollback()
            return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset Match and UserSwipe tables in the Dateabase application.")
    parser.add_argument('--force', '-f', action='store_true', help="Skip confirmation prompt")
    args = parser.parse_args()
    
    reset_matches_and_swipes(confirm=args.force) 