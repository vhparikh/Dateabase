"""
Test script to verify Pinecone connectivity and basic operations.
Run this script to check if your Pinecone setup is working correctly.
"""

import os
import pinecone
import cohere

# Generate embeddings using Cohere API
def get_test_embedding(text):
    """Generate an embedding using Cohere's API"""
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
        
        # Cohere's embed-english-v3.0 model produces 1024-dimensional vectors,
        # which matches our Pinecone index perfectly
        assert embedding_dim == 1024, f"Embedding dimension mismatch: {embedding_dim} != 1024"
        
        return embedding
        
    except Exception as e:
        print(f"Error generating embedding with Cohere API: {e}")
        # Return dummy vector as fallback
        print("Using fallback dummy vector of 1024 dimensions")
        return [0.1] * 1024

def test_pinecone_connection():
    """Test Pinecone connectivity and basic operations"""
    
    # Get Pinecone credentials from environment
    api_key = os.environ.get('PINECONE_API_KEY')
    # Check both variable names
    index_name = os.environ.get('PINECONE_INDEX') or os.environ.get('PINECONE_INDEX_NAME')
    
    if not api_key:
        print("ERROR: PINECONE_API_KEY environment variable is not set")
        return False
        
    if not index_name:
        print("ERROR: Neither PINECONE_INDEX nor PINECONE_INDEX_NAME environment variables are set")
        return False
    
    print(f"Testing Pinecone connection with index: {index_name}")
    
    try:
        # Initialize Pinecone client
        pc = pinecone.Pinecone(api_key=api_key)
        
        # List available indexes
        indexes = pc.list_indexes()
        print(f"Available indexes: {indexes}")
        
        if not indexes:
            print("WARNING: No indexes found in your Pinecone account")
            return False
            
        if index_name not in [idx.name for idx in indexes]:
            print(f"WARNING: Index '{index_name}' not found in your account")
            return False
        
        # Connect to the specified index
        index = pc.Index(index_name)
        
        # Get index stats
        stats = index.describe_index_stats()
        print(f"Index stats: {stats}")
        
        # Try a simple upsert using an embedding
        try:
            test_text = "This is a test vector to verify Pinecone connectivity"
            print(f"Generating test embedding for: {test_text}")
            
            # Generate a test embedding
            test_embedding = get_test_embedding(test_text)
            print(f"Generated test embedding with dimension: {len(test_embedding)}")
            
            # Create the test vector
            test_vector = {
                "id": "test_vector_1",
                "values": test_embedding,
                "metadata": {
                    "test": True, 
                    "purpose": "connectivity_test",
                    "text": test_text
                }
            }
            
            # Upsert the test vector
            print("Upserting test vector...")
            result = index.upsert(vectors=[test_vector])
            print(f"Test vector upsert successful: {result}")
            
            # Try a simple query
            print("Querying with test embedding...")
            query_result = index.query(
                vector=test_embedding,
                top_k=1,
                include_metadata=True
            )
            
            print(f"Test query successful: {query_result}")
            
            # Try to delete the test vector
            print("Deleting test vector...")
            delete_result = index.delete(ids=["test_vector_1"])
            print(f"Test vector deletion successful: {delete_result}")
            
            print("\nPinecone connection test PASSED! ✅")
            return True
            
        except Exception as e:
            print(f"Error during Pinecone operations: {e}")
            return False
            
    except Exception as e:
        print(f"Error connecting to Pinecone: {e}")
        return False

if __name__ == "__main__":
    test_pinecone_connection() 