"""
Utility script to index all existing experiences in Pinecone vector database.
This should be run once to populate the index with existing experiences.
New experiences will be automatically indexed when created.
"""

import os
import pinecone
import json
from app import app, index_experience
from database import db, Experience, User

def index_all_experiences():
    """Index all existing experiences in Pinecone"""
    
    # Initialize Pinecone
    pinecone_api_key = os.environ.get('PINECONE_API_KEY')
    pinecone_env = os.environ.get('PINECONE_ENV')
    pinecone_index = os.environ.get('PINECONE_INDEX')
    
    if not all([pinecone_api_key, pinecone_env, pinecone_index]):
        print("Error: Pinecone environment variables not set.")
        print("Make sure PINECONE_API_KEY, PINECONE_ENV, and PINECONE_INDEX are set.")
        return False
    
    try:
        print(f"Initializing Pinecone with index: {pinecone_index}")
        pinecone.init(api_key=pinecone_api_key, environment=pinecone_env)
        index = pinecone.Index(pinecone_index)
        
        with app.app_context():
            # Get all experiences
            experiences = Experience.query.all()
            print(f"Found {len(experiences)} experiences to index")
            
            success_count = 0
            error_count = 0
            
            for exp in experiences:
                try:
                    # Get the creator of the experience
                    creator = User.query.get(exp.user_id)
                    
                    # Index the experience in Pinecone
                    print(f"Indexing experience {exp.id} - {exp.experience_type} at {exp.location}")
                    result = index_experience(exp, creator)
                    
                    if result:
                        success_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    print(f"Error indexing experience {exp.id}: {e}")
                    error_count += 1
                    
            print(f"Indexing complete. Successfully indexed {success_count} experiences. Errors: {error_count}")
            return True
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    index_all_experiences() 