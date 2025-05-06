#!/usr/bin/env python3
"""
Script to list all users in the Heroku database for date-a-base-with-credits
"""

import os
import sys
from flask import Flask
from sqlalchemy import text

# Add the current directory to the path so we can import the database modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import database models
try:
    from backend.database import db, User
except ImportError:
    try:
        from database import db, User
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

def list_users():
    """List all users in the database"""
    with app.app_context():
        users = User.query.all()
        
        print(f"\n===== Found {len(users)} users in the database =====\n")
        
        for user in users:
            print(f"ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Name: {user.name}")
            print(f"NetID: {user.netid}")
            print(f"Gender: {user.gender}")
            print(f"Class Year: {user.class_year}")
            print(f"Onboarding Completed: {user.onboarding_completed}")
            print(f"Created At: {user.created_at}")
            print("-" * 50)

if __name__ == "__main__":
    list_users() 