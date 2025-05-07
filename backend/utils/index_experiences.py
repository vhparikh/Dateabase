"""
Utility script to index all existing experiences in Pinecone vector database.
This should be run once to populate the index with existing experiences.
New experiences will be automatically indexed when created.
"""

import os
import sys
import json
import pinecone
from cohere import Client as CohereClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from backend.database import User, Experience


if len(sys.argv) > 1:
    db_url = sys.argv[1]
else:
    db_url = os.environ.get('DATABASE_URL', '')
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)

if not db_url:
    print("Error: DATABASE_URL environment variable is not set.")
    sys.exit(1)

def get_experience_text(experience, creator=None):
    """
    Generate a simple text description of an experience for vector embedding.
    """
    # Only include experience type
    if experience.experience_type:
        return f"Experience type: {experience.experience_type}"
    else:
        return "No specific experience details"

def index_all_experiences():
    """Index all existing experiences in Pinecone"""
    
    pinecone_api_key = os.environ.get('PINECONE_API_KEY', '')
    pinecone_index_name = os.environ.get('PINECONE_INDEX', '')
    cohere_api_key = os.environ.get('COHERE_API_KEY', '')
    
    if not pinecone_api_key:
        print("Error: PINECONE_API_KEY environment variable is not set.")
        return False
    
    if not pinecone_index_name:
        print("Error: PINECONE_INDEX environment variable is not set.")
        return False
        
    if not cohere_api_key:
        print("Error: COHERE_API_KEY environment variable is not set.")
        return False
    
    try:
        # Initialize SQLAlchemy
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Initialize Pinecone
        pc = pinecone.Pinecone(api_key=pinecone_api_key)
        
        try:
            index = pc.Index(pinecone_index_name)
            print(f"Successfully connected to Pinecone index: {pinecone_index_name}")
        except Exception as e:
            print(f"Error connecting to Pinecone index: {e}")
            return False
        
        # Initialize Cohere
        co = CohereClient(cohere_api_key)
        
        # Retrieve all experiences
        experiences = session.query(Experience).all()
        print(f"Found {len(experiences)} experiences to index")
        
        success_count = 0
        error_count = 0
        
        # Create or update vector embeddings for each experience
        for exp in experiences:
            print(f"Processing experience {exp.id} - {exp.experience_type}")
            try:
                # Get the creator of the experience
                creator = session.query(User).filter_by(id=exp.user_id).first()
                if not creator:
                    print(f"Warning: Creator not found for experience {exp.id}, using partial data")
                else:
                    print(f"Found creator: {creator.name} (ID: {creator.id})")
                
                # Generate text description of the experience
                text_description = get_experience_text(exp)
                print(f"Generated text description: {text_description[:100]}...")
                
                # Create metadata for experience
                metadata = {
                    'id': exp.id,
                    'user_id': exp.user_id,
                    'experience_type': exp.experience_type,
                }
                
                # Generate embedding using Cohere
                response = co.embed(
                    texts=[text_description],
                    model="embed-english-v3.0",
                    input_type="search_document"
                )
                
                # Extract embedding
                embedding = response.embeddings[0]
                
                print(f"Generated embedding with dimension {len(embedding)}")
                
                # Create vector record
                vector = {
                    'id': f"exp_{exp.id}",
                    'values': embedding,
                    'metadata': {
                        **metadata,
                        'text': text_description
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
    print("Starting experience indexing script...")
    success = index_all_experiences()
    
    if success:
        print("Successfully indexed experiences in Pinecone")
        sys.exit(0)
    else:
        print("Failed to index experiences")
        sys.exit(1) 