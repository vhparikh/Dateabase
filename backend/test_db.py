from flask import Flask
from database import db, User, Experience, Match, UserSwipe
from datetime import datetime
import random

def test_db_connection():
    """Test basic database connection and operations"""
    app = Flask(__name__)
    
    # PostgreSQL connection string
    DATABASE_URL = "postgresql://ueaqcj622ro270:pf6999e838eb1f1f2e5af5b4b9d17b2fcdc2475e46597ea2d0dcdbd6bdb1e13af@ceqbglof0h8enj.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dc26u3dpl6nepd"
    
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the app with SQLAlchemy
    db.init_app(app)
    
    with app.app_context():
        try:
            print("\n=== Testing Database Connection ===")
            
            # Test 1: Create a test user
            print("\nTest 1: Creating test user...")
            test_user = User(
                username=f"testuser_{random.randint(1000,9999)}",
                name="Test User",
                gender="other",
                class_year=2025,
                interests="testing"
            )
            test_user.set_password("testpass123")
            db.session.add(test_user)
            db.session.commit()
            print(f"✓ Created user with ID: {test_user.id}")
            
            # Test 2: Create an experience
            print("\nTest 2: Creating test experience...")
            test_experience = Experience(
                user_id=test_user.id,
                experience_type="Test Activity",
                location="Test Location",
                description="This is a test experience",
                latitude=40.3573,
                longitude=-74.6672
            )
            db.session.add(test_experience)
            db.session.commit()
            print(f"✓ Created experience with ID: {test_experience.id}")
            
            # Test 3: Query the data back
            print("\nTest 3: Querying data...")
            user_query = User.query.filter_by(id=test_user.id).first()
            exp_query = Experience.query.filter_by(id=test_experience.id).first()
            print(f"✓ Retrieved user: {user_query.username}")
            print(f"✓ Retrieved experience: {exp_query.location}")
            
            # Test 4: Update data
            print("\nTest 4: Updating data...")
            user_query.interests = "updated testing interests"
            db.session.commit()
            print("✓ Updated user interests")
            
            # Test 5: Delete test data
            print("\nTest 5: Cleaning up test data...")
            db.session.delete(exp_query)
            db.session.delete(user_query)
            db.session.commit()
            print("✓ Deleted test data")
            
            print("\n✅ All tests completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Error during testing: {str(e)}")
            db.session.rollback()
            raise e

if __name__ == "__main__":
    test_db_connection() 