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

# Import User and Experience from database.py
from database import User, Experience

# Ensure environment variables are accessible
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
    Generate a rich text description of an experience including both the experience details
    and comprehensive information about the creator.
    
    This combined representation enables searching for experiences based on both
    the experience itself and the characteristics of the person who created it.
    """
    exp_parts = []
    
    # EXPERIENCE DETAILS
    
    # Basic experience info with stronger emphasis
    if experience.experience_type:
        exp_parts.append(f"Experience type: {experience.experience_type}")
    
    if experience.location:
        exp_parts.append(f"Location: {experience.location}")
    
    if experience.description:
        exp_parts.append(f"Description: {experience.description}")
    
    # Add coordinates if available for better location matching
    if experience.latitude and experience.longitude:
        exp_parts.append(f"Coordinates: {experience.latitude}, {experience.longitude}")
    
    # CREATOR DETAILS (comprehensive profile)
    if creator:
        creator_parts = []
        
        if creator.name:
            creator_parts.append(f"Creator name: {creator.name}")
        
        if creator.gender:
            creator_parts.append(f"Creator gender: {creator.gender}")
        
        if creator.class_year:
            creator_parts.append(f"Creator class year: {creator.class_year}")
        
        if creator.major:
            creator_parts.append(f"Creator major: {creator.major}")
        
        if creator.interests:
            creator_parts.append(f"Creator interests: {creator.interests}")
        
        # Add other profile fields if available
        if hasattr(creator, 'hometown') and creator.hometown:
            creator_parts.append(f"Creator hometown: {creator.hometown}")
            
        # Add creator's other experiences to provide more context
        other_experiences = [exp for exp in creator.experiences 
                             if exp.id != experience.id]
        if other_experiences:
            other_exp_types = [exp.experience_type for exp in other_experiences 
                              if exp.experience_type]
            unique_types = list(set(other_exp_types))
            if unique_types:
                creator_parts.append(f"Creator's other experience types: {', '.join(unique_types[:5])}")
        
        # Add the creator details to the experience parts
        if creator_parts:
            exp_parts.append("CREATOR PROFILE: " + " ".join(creator_parts))
    
    # Join all parts into a single text description
    if exp_parts:
        return " ".join(exp_parts)
    else:
        return "No specific experience details"

def index_all_experiences():
    """Index all existing experiences in Pinecone"""
    # Only proceed if the Pinecone API key and index name are set
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
        # Initialize SQLAlchemy with the database URL
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Initialize Pinecone with the API key
        pc = pinecone.Pinecone(api_key=pinecone_api_key)
        
        # Check if the index exists
        try:
            index = pc.Index(pinecone_index_name)
            print(f"Successfully connected to Pinecone index: {pinecone_index_name}")
        except Exception as e:
            print(f"Error connecting to Pinecone index: {e}")
            return False
        
        # Initialize Cohere client
        co = CohereClient(cohere_api_key)
        
        # Retrieve all experiences from the database
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
                text_description = get_experience_text(exp, creator)
                print(f"Generated text description: {text_description[:100]}...")
                
                # Create metadata for the experience
                metadata = {
                    'id': exp.id,
                    'user_id': exp.user_id,
                    'experience_type': exp.experience_type,
                    'location': exp.location,
                    'description': exp.description if exp.description else "",
                    'created_at': exp.created_at.isoformat() if exp.created_at else "",
                }
                
                # Add creator metadata if available
                if creator:
                    metadata.update({
                        'creator_name': creator.name if creator.name else "",
                        'creator_gender': creator.gender if creator.gender else "",
                        'creator_class_year': creator.class_year if creator.class_year else 0,
                        'creator_major': creator.major if creator.major else "",
                    })
                    # Add additional creator metadata for better filtering
                    if creator.hometown:
                        metadata['creator_hometown'] = creator.hometown
                    if creator.interests:
                        metadata['creator_interests'] = creator.interests
                
                # Generate embedding using Cohere API
                response = co.embed(
                    texts=[text_description],
                    model="embed-english-v3.0",
                    input_type="search_document"
                )
                
                # Extract embedding from response
                embedding = response.embeddings[0]
                
                print(f"Generated embedding with dimension {len(embedding)}")
                
                # Create vector record with the correct format for SDK v3
                vector = {
                    'id': f"exp_{exp.id}",
                    'values': embedding,  # Real embedding
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
    print("Starting experience indexing script...")
    success = index_all_experiences()
    
    if success:
        print("Successfully indexed experiences in Pinecone")
        sys.exit(0)
    else:
        print("Failed to index experiences")
        sys.exit(1) 