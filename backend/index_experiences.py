"""
Utility script to index all existing experiences in Pinecone vector database.
This should be run once to populate the index with existing experiences.
New experiences will be automatically indexed when created.
"""

import os
import pinecone
import json
from app import app, get_experience_text
from database import db, Experience, User

def index_all_experiences():
    """Index all existing experiences in Pinecone"""
    
    # Initialize Pinecone
    pinecone_api_key = os.environ.get('PINECONE_API_KEY')
    # Check both variable names
    pinecone_index_name = os.environ.get('PINECONE_INDEX') or os.environ.get('PINECONE_INDEX_NAME')
    
    if not all([pinecone_api_key, pinecone_index_name]):
        print("Error: Pinecone environment variables not set.")
        if not pinecone_api_key:
            print("PINECONE_API_KEY is missing")
        if not pinecone_index_name:
            print("Both PINECONE_INDEX and PINECONE_INDEX_NAME are missing")
        print("Make sure PINECONE_API_KEY and either PINECONE_INDEX or PINECONE_INDEX_NAME are set.")
        return False
    
    try:
        print(f"Initializing Pinecone with index: {pinecone_index_name}")
        # Updated initialization pattern
        pc = pinecone.Pinecone(api_key=pinecone_api_key)
        index = pc.Index(pinecone_index_name)
        
        # Test connection with a simple query to verify index is accessible
        try:
            # Use a dummy vector for the test query
            dummy_vector = [0.1] * 1024  # 1024-dimensional vector
            test_result = index.query(top_k=1, vector=dummy_vector)
            print(f"Connection test successful: {test_result}")
        except Exception as test_e:
            print(f"Warning: Could not perform test query: {test_e}")
        
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
                    
                    # Generate text description
                    text_description = get_experience_text(exp, creator)
                    
                    # Create metadata
                    metadata = {
                        'id': exp.id,
                        'user_id': exp.user_id,
                        'experience_type': exp.experience_type,
                        'location': exp.location,
                        'description': exp.description if exp.description else "",
                        'created_at': exp.created_at.isoformat() if exp.created_at else "",
                    }
                    
                    # Add creator info to metadata if available
                    if creator:
                        metadata.update({
                            'creator_name': creator.name if creator.name else "",
                            'creator_gender': creator.gender if creator.gender else "",
                            'creator_class_year': creator.class_year if creator.class_year else 0, 
                            'creator_major': creator.major if creator.major else "",
                        })
                    
                    # Create vector record with the correct format for SDK v3
                    vector = {
                        'id': f"exp_{exp.id}",
                        'values': [0.1] * 1024,  # Dummy vector with 1024 dimensions
                        'metadata': {
                            **metadata,
                            'text': text_description  # Text goes in metadata
                        }
                    }
                    
                    # Upsert to Pinecone
                    print(f"Indexing experience {exp.id} - {exp.experience_type} at {exp.location}")
                    result = index.upsert(vectors=[vector])
                    
                    print(f"Result: {result}")
                    success_count += 1
                        
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