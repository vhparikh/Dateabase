import os
import cohere
from datetime import datetime, timedelta, timezone
import json
import pinecone


from ..database import db, init_db, User, Experience, Match, UserSwipe, UserImage

# Configure Pinecone
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY', '')
PINECONE_ENV = os.environ.get('PINECONE_ENV', '')
PINECONE_INDEX = os.environ.get('PINECONE_INDEX', '')

# Initialize Pinecone if we have the required environment variables
pinecone_initialized = False
pinecone_index = None

if PINECONE_API_KEY and PINECONE_INDEX:
    try:
        # Initialization for Pinecone
        pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
        pinecone_index = pc.Index(PINECONE_INDEX)
        pinecone_initialized = True
        print(f"Pinecone initialized with index: {PINECONE_INDEX}")
    except Exception as e:
        print(f"Error initializing Pinecone: {e}")
else:
    print("Pinecone environment variables not set. Vector search functionality unavailable.")
    if not PINECONE_API_KEY:
        print("PINECONE_API_KEY is missing")
    if not PINECONE_INDEX:
        print("Both PINECONE_INDEX and PINECONE_INDEX_NAME are missing")

# Embedding function using Cohere API
def get_embedding(text):
    """Generate embeddings using Cohere's embedding API"""
    try:
        # Get API key from environment variable
        api_key = os.environ.get("COHERE_API_KEY")
        if not api_key:
            print("ERROR: COHERE_API_KEY environment variable not set")
            # Return dummy vector as fallback
            print("Using fallback dummy vector of 1024 dimensions")
            return [0.1] * 1024
            
        # Initialize Cohere client
        co = cohere.Client(api_key)
        
        # Generate embedding using Cohere's API
        print(f"Generating embedding via Cohere API for text: {text[:50]}...")
        response = co.embed(
            texts=[text],
            model="embed-english-v3.0",
            input_type="search_document"
        )
        
        # Extract the embedding from the response
        embedding = response.embeddings[0]
        
        # Verify embedding dimension
        embedding_dim = len(embedding)
        print(f"Generated embedding with dimension {embedding_dim}")
        
        assert embedding_dim == 1024, f"Embedding dimension mismatch: {embedding_dim} != 1024"
        
        return embedding
        
    except Exception as e:
        print(f"Error generating embedding with Cohere API: {e}")
        # Return dummy vector as fallback
        print("Using fallback dummy vector of 1024 dimensions")
        return [0.1] * 1024
    
def get_user_preference_text(user):
    """
    Generate a simple text description of user preferences for vector embedding.
    """
    # Process experience type preferences
    if user.experience_type_prefs:
        
        exp_prefs = json.loads(user.experience_type_prefs)
        
        exp_types = [exp_type for exp_type, is_selected in exp_prefs.items() if is_selected]
        if exp_types:
            return f"Preferred experience types: {', '.join(exp_types)}"
    
    return "No specific preferences"

def get_experience_text(experience, creator=None):
    """
    Generate a simple text description of an experience for vector embedding.
    """

    if experience.experience_type:
        return f"Experience type: {experience.experience_type}"
    else:
        return "No specific experience details"

def index_experience(experience, creator=None):
    """
    Index an experience in Pinecone for vector search.
    """
    if not pinecone_initialized or not pinecone_index:
        print(f"Experience {experience.id}: Pinecone not initialized. Cannot index experience.")
        return False
    
    try:
        
        text_description = get_experience_text(experience)
        print(f"Experience {experience.id}: Generated text description: {text_description[:100]}...")
        
        metadata = {
            'id': experience.id,
            'user_id': experience.user_id,
            'experience_type': experience.experience_type,
        }
        
        print(f"Experience {experience.id}: Created metadata")
        
        print(f"Experience {experience.id}: Generating embedding")
        embedding = get_embedding(text_description)
        print(f"Experience {experience.id}: Generated embedding with dimension {len(embedding)}")
        
        # Create the Pinecone vector record with embedding
        record = {
            'id': f"exp_{experience.id}",
            'values': embedding,
            'metadata': {
                **metadata,
                'text': text_description
            }
        }
        
        print(f"Experience {experience.id}: Created vector record")
        
        # Upsert the record into Pinecone
        try:
            print(f"Experience {experience.id}: Attempting to upsert to Pinecone")
            result = pinecone_index.upsert(
                vectors=[record],
            )
            print(f"Experience {experience.id}: Successfully indexed in Pinecone. Response: {result}")
            return True
        except Exception as e:
            print(f"Experience {experience.id}: Error in Pinecone upsert operation: {e}")
            return False
            
    except Exception as e:
        print(f"Experience {experience.id}: Error preparing data for Pinecone indexing: {e}")
        return False

def delete_experience_from_pinecone(experience_id):
    """
    Delete an experience from Pinecone vector index.
    """
    if not pinecone_initialized or not pinecone_index:
        print(f"Experience {experience_id}: Pinecone not initialized. Cannot delete experience from index.")
        return False
    
    try:
        # Format the ID as it appears in Pinecone
        pinecone_id = f"exp_{experience_id}"
        
        # Delete the vector from Pinecone
        print(f"Experience {experience_id}: Attempting to delete from Pinecone")
        result = pinecone_index.delete(ids=[pinecone_id])
        
        print(f"Experience {experience_id}: Successfully deleted from Pinecone. Response: {result}")
        return True
    except Exception as e:
        print(f"Experience {experience_id}: Error deleting from Pinecone: {e}")
        return False

def get_personalized_experiences(user, top_k=20):
    """
    Query Pinecone with user preferences to get personalized experience recommendations.
    """
    if not pinecone_initialized or not pinecone_index:
        print(f"User {user.id}: Pinecone not initialized. Cannot query for personalized experiences.")
        return None
    
    try:

        preference_embedding = None
        need_new_embedding = True
        cache_new_embedding = False
        
        # Check if we have a cached preference vector
        if user.preference_vector and user.preference_vector_updated_at:
            print(f"User {user.id}: Found cached preference vector from {user.preference_vector_updated_at}")
            
            # Deserialize the cached vector from JSON
            try:
                preference_embedding = json.loads(user.preference_vector)
                vector_dimension = len(preference_embedding)
                print(f"User {user.id}: Loaded cached preference vector with dimension {vector_dimension}")
                
                # Make sure the vector has the correct dimension
                if vector_dimension == 1024:
                    # Use the cached vector
                    latest_swipe = UserSwipe.query.filter_by(user_id=user.id).order_by(
                        UserSwipe.created_at.desc()
                    ).first()
                    
                    if latest_swipe and latest_swipe.created_at > user.preference_vector_updated_at:
                        print(f"User {user.id}: Found newer swipes than cached vector, regenerating")
                        need_new_embedding = True
                        cache_new_embedding = True
                    else:
                        print(f"User {user.id}: Using cached preference vector from {user.preference_vector_updated_at}")
                        need_new_embedding = False
                else:
                    print(f"User {user.id}: Cached vector dimension mismatch: {vector_dimension} != 1024, regenerating")
                    need_new_embedding = True
                    cache_new_embedding = True
            except Exception as e:
                print(f"User {user.id}: Error loading cached preference vector: {e}")
                need_new_embedding = True
                cache_new_embedding = True
        else:
            print(f"User {user.id}: No cached preference vector found, generating new one")
            need_new_embedding = True
            cache_new_embedding = True
        
        # Generate a new preference embedding if needed
        if need_new_embedding:
            # Generate simplified text description of user preferences
            preference_text = get_user_preference_text(user)
            print(f"User {user.id}: Generated preference text: {preference_text[:100]}...")
            
            # Generate embedding for user preferences using Cohere
            print(f"User {user.id}: Generating new preference embedding")
            preference_embedding = get_embedding(preference_text)
            print(f"User {user.id}: Generated preference embedding with dimension {len(preference_embedding)}")
            
            # Cache the new embedding if needed
            if cache_new_embedding:
                try:
                    import json
                    user.preference_vector = json.dumps(preference_embedding)
                    user.preference_vector_updated_at = datetime.utcnow()
                    db.session.commit()
                    print(f"User {user.id}: Cached new preference vector at {user.preference_vector_updated_at}")
                except Exception as e:
                    print(f"User {user.id}: Error caching preference vector: {e}")
                    db.session.rollback()
                    # Continue even if caching fails
        
        # Filter to exclude experiences created by the user - this is the only filter we need
        filter_conditions = {
            "user_id": {"$ne": user.id}  # Base filter: exclude user's own experiences
        }
        
        # Log the exact filter being used
        print(f"User {user.id}: Using Pinecone filter: {filter_conditions}")
        
        # Query Pinecone for similar vectors
        try:
            print(f"User {user.id}: Querying Pinecone with preference embedding")
            query_results = pinecone_index.query(
                top_k=top_k * 2,
                vector=preference_embedding,
                filter=filter_conditions,
                include_metadata=True
            )
            
            print(f"User {user.id}: Pinecone query returned {len(query_results.get('matches', []))} matches")
            
            # Extract and process the matching experiences
            matches = []
            for match in query_results.get('matches', []):
                exp_id = int(match['id'].split('_')[1]) if match['id'].startswith('exp_') else None
                if exp_id:
                    
                    # Format the match with ID, score, and metadata
                    matches.append({
                        'id': exp_id,
                        'score': match['score'],
                        'metadata': match['metadata']
                    })
            
            print(f"User {user.id}: Found {len(matches)} valid experience matches")
            
            # Return the matches sorted by score
            return matches
            
        except Exception as e:
            print(f"User {user.id}: Error querying Pinecone: {e}")
            return None
            
    except Exception as e:
        print(f"User {user.id}: Error in get_personalized_experiences: {e}")
        return None