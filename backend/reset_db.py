from app import app, db
import os

# Remove existing database file if it exists
if os.path.exists('dateabase.db'):
    os.remove('dateabase.db')
    print("Removed existing database")

# Create database with app context
with app.app_context():
    db.create_all()
    print("Created new database with updated schema")
    
    # Seed the demo user
    from app import seed_demo_user
    seed_demo_user()
    print("Added demo user to database")
    
    # Create demo matches if available
    try:
        from app import create_demo_matches
        create_demo_matches()
        print("Created demo matches")
    except Exception as e:
        print(f"Note: Could not create demo matches: {e}")
        
print("Database reset complete!") 