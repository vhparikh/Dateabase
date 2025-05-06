#!/usr/bin/env python3
"""
Script to delete all experiences created by specific users:
- Sherm William (NetID: zm9322, ID: 10)
- Hk4638 User (NetID: hk4638, ID: 11)
"""

import os
import sys
from flask import Flask

# Add the current directory to the path so we can import the database modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import database models
try:
    from backend.database import db, User, Experience, UserSwipe, Match
except ImportError:
    try:
        from database import db, User, Experience, UserSwipe, Match
    except ImportError:
        print("Error: Unable to import database modules. Make sure you run this script from the project root.")
        sys.exit(1)

# Create a Flask app context for database access
app = Flask(__name__)

# Database URL for Heroku
DATABASE_URL = "postgres://ueaqcj622ro270:pf6999e838eb1f1f2e5af5b4b9d17b2fcdc2475e46597ea2d0dcdbd6bdb1e13af@ceqbglof0h8enj.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dc26u3dpl6nepd"

# Heroku prepends "postgres://" but SQLAlchemy expects "postgresql://"
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the app with SQLAlchemy
db.init_app(app)

def delete_user_experiences(user_ids):
    """Delete all experiences created by the specified users"""
    with app.app_context():
        # Get the users to confirm who we're deleting from
        users = User.query.filter(User.id.in_(user_ids)).all()
        
        if not users:
            print("No users found with the specified IDs.")
            return
        
        print("Found users:")
        for user in users:
            print(f"- ID: {user.id}, Name: {user.name}, NetID: {user.netid}")
        
        # Double-check with the user before proceeding
        confirmation = input("\nAre you sure you want to delete ALL experiences for these users? (y/n): ").strip().lower()
        if confirmation != 'y':
            print("Operation cancelled.")
            return
        
        # Get experiences for each user
        all_experiences = []
        for user in users:
            experiences = Experience.query.filter_by(user_id=user.id).all()
            all_experiences.extend(experiences)
            print(f"\nUser {user.name} (ID: {user.id}) has {len(experiences)} experiences")
        
        if not all_experiences:
            print("\nNo experiences found for the specified users.")
            return
        
        # Get experience IDs for deletion
        experience_ids = [exp.id for exp in all_experiences]
        
        # First delete related UserSwipe records that reference these experiences
        swipes_deleted = 0
        swipes = UserSwipe.query.filter(UserSwipe.experience_id.in_(experience_ids)).all()
        for swipe in swipes:
            print(f"Deleting swipe: ID {swipe.id}, User {swipe.user_id}, Experience {swipe.experience_id}")
            db.session.delete(swipe)
            swipes_deleted += 1
        
        # Delete related Match records that reference these experiences
        matches_deleted = 0
        matches = Match.query.filter(Match.experience_id.in_(experience_ids)).all()
        for match in matches:
            print(f"Deleting match: ID {match.id}, Users {match.user1_id}-{match.user2_id}, Experience {match.experience_id}")
            db.session.delete(match)
            matches_deleted += 1
        
        # Commit the deletion of related records first
        if swipes_deleted > 0 or matches_deleted > 0:
            db.session.commit()
            print(f"\nDeleted {swipes_deleted} related swipes and {matches_deleted} related matches")
        
        # Now delete the experiences
        experiences_deleted = 0
        for user in users:
            experiences = Experience.query.filter_by(user_id=user.id).all()
            
            print(f"\nDeleting experiences for {user.name} (NetID: {user.netid}):")
            for exp in experiences:
                print(f"- ID: {exp.id}, Type: {exp.experience_type}, Location: {exp.location}")
                db.session.delete(exp)
                experiences_deleted += 1
        
        # Commit changes
        if experiences_deleted > 0:
            db.session.commit()
            print(f"\nSuccessfully deleted {experiences_deleted} experiences.")
        else:
            print("\nNo experiences found or all were already deleted.")

if __name__ == "__main__":
    # User IDs for Sherm William (10) and Hk4638 User (11)
    target_user_ids = [10, 11]
    delete_user_experiences(target_user_ids) 