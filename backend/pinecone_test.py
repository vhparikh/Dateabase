"""
Test script to verify Pinecone connectivity and basic operations.
Run this script to check if your Pinecone setup is working correctly.
"""

import os
import pinecone

# Simple embedding helper for testing
def get_test_embedding(text):
    """Generate a simple test embedding for the given text.
    This is just for testing - not for real usage"""
    # Create a deterministic but somewhat varied vector based on the text
    # This is NOT a real embedding, just a test vector
    import hashlib
    
    # Use a hash of the text to seed the vector values
    hash_obj = hashlib.md5(text.encode())
    hash_val = int(hash_obj.hexdigest(), 16)
    
    # Create a 1024-dimensional vector with values between -1 and 1
    vector = []
    for i in range(1024):
        # Use the hash and position to generate a value
        val = ((hash_val + i) % 1000) / 500.0 - 1.0
        vector.append(val)
    
    return vector

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