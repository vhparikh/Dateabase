from app import app, db, User, Experience, Match, UserSwipe
from datetime import datetime, timedelta
import random
import json

# Sample data
users = [
    {
        "name": "Alex Johnson",
        "gender": "male",
        "class_year": 2024,
        "interests": "hiking, coffee, movies, studying, photography"
    },
    {
        "name": "Sophia Chen",
        "gender": "female",
        "class_year": 2025,
        "interests": "reading, coffee, art, cooking, tennis"
    },
    {
        "name": "James Wilson",
        "gender": "male",
        "class_year": 2023,
        "interests": "basketball, music, coding, gaming, hiking"
    },
    {
        "name": "Emma Davis",
        "gender": "female",
        "class_year": 2024,
        "interests": "yoga, volunteering, coffee, movies, traveling"
    },
    {
        "name": "Michael Brown",
        "gender": "male",
        "class_year": 2025,
        "interests": "soccer, history, coffee, biking, concerts"
    }
]

experiences = [
    {
        "experience_type": "Coffee",
        "location": "Small World Coffee",
        "description": "Looking for someone to grab coffee with between classes. I'm usually free on Tuesday and Thursday afternoons."
    },
    {
        "experience_type": "Study Session",
        "location": "Firestone Library",
        "description": "Need a study buddy for upcoming finals. I'm studying Economics and could use someone to quiz me!"
    },
    {
        "experience_type": "Dinner",
        "location": "Tacoria",
        "description": "Anyone up for tacos? I've been craving them all week and would love some company."
    },
    {
        "experience_type": "Hiking",
        "location": "Institute Woods",
        "description": "Planning a weekend hike to enjoy the fall colors. Moderate pace, about 2 hours total."
    },
    {
        "experience_type": "Movie",
        "location": "Princeton Garden Theatre",
        "description": "The new Marvel movie is out! Looking for fellow fans to watch it with this Saturday evening."
    },
    {
        "experience_type": "Concert",
        "location": "Richardson Auditorium",
        "description": "There's a jazz ensemble playing this Friday. I have an extra ticket if anyone is interested."
    },
    {
        "experience_type": "Sports",
        "location": "Princeton Stadium",
        "description": "Going to the big game this weekend. Would love to have someone to cheer with!"
    }
]

def seed_database():
    # Clear database
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        print("Adding users...")
        created_users = []
        for user_data in users:
            user = User(
                name=user_data["name"],
                gender=user_data["gender"],
                class_year=user_data["class_year"],
                interests=user_data["interests"]
            )
            db.session.add(user)
            db.session.flush()  # Get the ID without committing
            created_users.append(user)
        
        db.session.commit()
        print(f"Added {len(created_users)} users")
        
        print("Adding experiences...")
        created_experiences = []
        for i, exp_data in enumerate(experiences):
            # Assign each experience to a different user
            user = created_users[i % len(created_users)]
            exp = Experience(
                user_id=user.id,
                experience_type=exp_data["experience_type"],
                location=exp_data["location"],
                description=exp_data["description"],
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 10))
            )
            db.session.add(exp)
            db.session.flush()
            created_experiences.append(exp)
        
        db.session.commit()
        print(f"Added {len(created_experiences)} experiences")
        
        print("Adding swipes and matches...")
        # Create some swipes and matches
        matches_count = 0
        swipes_count = 0
        
        for user in created_users:
            # Each user swipes on 2-4 experiences
            for _ in range(random.randint(2, 4)):
                # Skip experiences created by this user
                potential_experiences = [exp for exp in created_experiences if exp.user_id != user.id]
                if not potential_experiences:
                    continue
                    
                experience = random.choice(potential_experiences)
                direction = random.choice([True, False])  # True for right, False for left
                
                # Add swipe
                swipe = UserSwipe(
                    user_id=user.id,
                    experience_id=experience.id,
                    direction=direction,
                    created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 24))
                )
                db.session.add(swipe)
                swipes_count += 1
                
                # If right swipe, check if the creator has also swiped right (50% chance)
                if direction and random.random() > 0.5:
                    # Create a match
                    match = Match(
                        user1_id=user.id,
                        user2_id=experience.user_id,
                        experience_id=experience.id,
                        status='confirmed',
                        created_at=datetime.utcnow() - timedelta(hours=random.randint(0, 12))
                    )
                    db.session.add(match)
                    matches_count += 1
        
        db.session.commit()
        print(f"Added {swipes_count} swipes and {matches_count} matches")
        
        print("Database seeded successfully!")

if __name__ == "__main__":
    seed_database() 