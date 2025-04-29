#!/usr/bin/env python3
"""
Reindex Data Script

This script:
1. Regenerates vectors for all experiences in the database
2. Regenerates preference vectors for all users in the database
3. Ensures all data is properly indexed in Pinecone for personalized recommendations

Usage:
    python reindex_data.py
"""

import os
import sys
import json
from datetime import datetime
import time
import numpy as np
from sqlalchemy import func

# Add the backend directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from the app
from app import app, db, User, Experience, pinecone_initialized, pinecone_index
from app import get_embedding, get_user_preference_text, get_experience_text, index_experience

def reindex_experiences():
    """Reindex all experiences in the database"""
    
    with app.app_context():
        print("\n===== REINDEXING EXPERIENCES =====")
        # Get all experiences
        experiences = Experience.query.all()
        print(f"Found {len(experiences)} experiences to process")
        
        success_count = 0
        error_count = 0
        
        for i, exp in enumerate(experiences):
            print(f"\nProcessing experience {i+1}/{len(experiences)}: ID {exp.id}, Type: {exp.experience_type}")
            
            try:
                # Use simplified indexing function that only uses experience type
                result = index_experience(exp)
                
                if result:
                    print(f"  ✅ Successfully indexed experience {exp.id}")
                    success_count += 1
                else:
                    print(f"  ❌ Failed to index experience {exp.id}")
                    error_count += 1
                
                # Add a small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ❌ Error processing experience {exp.id}: {str(e)}")
                error_count += 1
        
        print(f"\nExperience reindexing complete: {success_count} successful, {error_count} failed")
        return success_count, error_count

def regenerate_user_preference_vectors():
    """Regenerate preference vectors for all users"""
    
    with app.app_context():
        print("\n===== REGENERATING USER PREFERENCE VECTORS =====")
        # Get all users
        users = User.query.all()
        print(f"Found {len(users)} users to process")
        
        success_count = 0
        error_count = 0
        
        for i, user in enumerate(users):
            print(f"\nProcessing user {i+1}/{len(users)}: ID {user.id}, Name: {user.name}")
            
            try:
                # Generate preference text
                preference_text = get_user_preference_text(user)
                if not preference_text or preference_text == "No specific preferences":
                    print(f"  ⚠️ User {user.id} has no specific preferences, skipping")
                    continue
                
                print(f"  Generated preference text: {preference_text[:100]}...")
                
                # Generate embedding if Pinecone is initialized
                if pinecone_initialized:
                    try:
                        print(f"  Generating preference embedding...")
                        preference_embedding = get_embedding(preference_text)
                        print(f"  Generated embedding with dimension {len(preference_embedding)}")
                        
                        # Update user with new preference vector
                        user.preference_vector = json.dumps(preference_embedding)
                        user.preference_vector_updated_at = datetime.utcnow()
                        db.session.commit()
                        
                        print(f"  ✅ Successfully updated preference vector for user {user.id}")
                        success_count += 1
                    except Exception as e:
                        print(f"  ❌ Error generating embedding: {str(e)}")
                        error_count += 1
                else:
                    print("  ⚠️ Pinecone not initialized, skipping embedding generation")
                    error_count += 1
                
                # Add a small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ❌ Error processing user {user.id}: {str(e)}")
                error_count += 1
        
        print(f"\nUser preference vector regeneration complete: {success_count} successful, {error_count} failed")
        return success_count, error_count

def test_retrieval():
    """Test retrieval of recommendations for a few users"""
    
    with app.app_context():
        print("\n===== TESTING VECTOR RETRIEVAL =====")
        
        # Test for a few random users with preference vectors
        users = User.query.filter(User.preference_vector != None).order_by(func.random()).limit(3).all()
        
        if not users:
            print("No users with preference vectors found. Skipping retrieval test.")
            return
            
        print(f"Testing retrieval for {len(users)} random users")
        
        for user in users:
            print(f"\nUser {user.id}: {user.name}")
            
            # Get user's experience type preferences
            user_preferred_exp_types = []
            if user.experience_type_prefs:
                try:
                    # Try as JSON
                    exp_prefs = json.loads(user.experience_type_prefs)
                    if isinstance(exp_prefs, dict):
                        user_preferred_exp_types = [exp_type for exp_type, is_selected in exp_prefs.items() if is_selected]
                    elif isinstance(exp_prefs, list):
                        user_preferred_exp_types = exp_prefs
                except:
                    # Fallback
                    if isinstance(user.experience_type_prefs, str):
                        if ',' in user.experience_type_prefs:
                            user_preferred_exp_types = [x.strip() for x in user.experience_type_prefs.split(',') if x.strip()]
                        else:
                            user_preferred_exp_types = [user.experience_type_prefs.strip()]
            
            print(f"  User's preferred experience types: {user_preferred_exp_types}")
            
            try:
                if not pinecone_initialized:
                    print("  ⚠️ Pinecone not initialized. Skipping test.")
                    continue
                    
                # Get the user's preference vector
                preference_embedding = json.loads(user.preference_vector)
                print(f"  User has preference vector with dimension {len(preference_embedding)}")
                
                # Retrieve from Pinecone
                print(f"  Querying Pinecone for similar experiences...")
                
                # Filter conditions - only exclude user's own experiences
                filter_conditions = {
                    "user_id": {"$ne": user.id}  # Base filter: exclude user's own experiences
                }
                
                # Query Pinecone
                query_results = pinecone_index.query(
                    top_k=5,  # Just get the top 5 for testing
                    vector=preference_embedding,
                    filter=filter_conditions,
                    include_metadata=True
                )
                
                # Process the results
                matches = query_results.get('matches', [])
                
                if not matches:
                    print("  ⚠️ No matches found from Pinecone")
                    continue
                
                print(f"  Found {len(matches)} matches from Pinecone")
                for i, match in enumerate(matches):
                    exp_id = int(match['id'].split('_')[1]) if match['id'].startswith('exp_') else None
                    if exp_id:
                        exp = Experience.query.get(exp_id)
                        if exp:
                            match_reason = "Based on vector similarity"
                            if exp.experience_type in user_preferred_exp_types:
                                match_reason = f"Matches preference for {exp.experience_type} experiences"
                            
                            print(f"    {i+1}. Experience {exp.id}: {exp.experience_type} at {exp.location}")
                            print(f"       Score: {match['score']:.4f}, Reason: {match_reason}")
                
            except Exception as e:
                print(f"  ❌ Error testing retrieval for user {user.id}: {str(e)}")

def main():
    print("=" * 80)
    print("EXPERIENCE AND USER PREFERENCE REINDEXING TOOL")
    print("=" * 80)
    
    if not pinecone_initialized:
        print("\n⚠️ WARNING: Pinecone is not initialized! Vector search functionality will not work.")
        proceed = input("\nDo you want to continue anyway? (y/n): ")
        if proceed.lower() != 'y':
            print("Exiting.")
            return
    
    print("\nThis script will:")
    print("1. Reindex all experiences in the database")
    print("2. Regenerate preference vectors for all users")
    print("3. Test recommendation retrieval for some users")
    
    proceed = input("\nDo you want to proceed? (y/n): ")
    if proceed.lower() != 'y':
        print("Exiting.")
        return
    
    start_time = time.time()
    
    # Reindex experiences
    exp_success, exp_error = reindex_experiences()
    
    # Regenerate user preference vectors
    user_success, user_error = regenerate_user_preference_vectors()
    
    # Test retrieval
    test_retrieval()
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print("\n" + "=" * 80)
    print("REINDEXING SUMMARY")
    print("=" * 80)
    print(f"Experiences reindexed: {exp_success} successful, {exp_error} failed")
    print(f"User preferences regenerated: {user_success} successful, {user_error} failed")
    print(f"Total time elapsed: {elapsed_time:.2f} seconds")
    print("\nReindexing complete!")

if __name__ == "__main__":
    main() 