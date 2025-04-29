from flask import Blueprint, request, jsonify, current_app
from flask_cors import CORS
from functools import wraps
from datetime import datetime

# Import login_required decorator
from .auth_utils import login_required

# Import database models
try:
    # Try local import first (for local development)
    from database import db, User, Experience, Match, UserSwipe, UserImage, add_new_columns, drop_unused_columns
    from recommender import index_experience, get_personalized_experiences, get_embedding, get_user_preference_text, get_experience_text
    import recommender
except ImportError:
    # Fall back to package import (for Heroku)
    from backend.database import db, User, Experience, Match, UserSwipe, UserImage, add_new_columns, drop_unused_columns
    from backend.recommender import index_experience, get_personalized_experiences, get_embedding, get_user_preference_text, get_experience_text
    import backend.recommender

swipe_bp = Blueprint('swipe_routes', __name__)

@swipe_bp.route('/api/swipes', methods=['POST'])
@login_required()
def record_swipe(current_user_id=None):
    """
    Record a user's swipe on an experience (like or dislike).
    
    If the user likes an experience, also check if the creator has liked any of the
    user's experiences to create a match.
    """
    data = request.json
    
    print(f"DEBUG: record_swipe called with data: {data} and user_id: {current_user_id}")
    
    # Validate required fields
    if not data or 'experience_id' not in data or 'is_like' not in data:
        print(f"DEBUG: Missing required fields in data: {data}")
        return jsonify({'detail': 'Missing required fields'}), 400
    
    try:
        experience_id = data['experience_id']
        is_like = data['is_like']
        
        print(f"DEBUG: Processing swipe - user: {current_user_id}, exp: {experience_id}, is_like: {is_like}")
        
        # Check if experience exists
        experience = Experience.query.get(experience_id)
        if not experience:
            print(f"DEBUG: Experience {experience_id} not found")
            return jsonify({'detail': 'Experience not found'}), 404
        
        print(f"DEBUG: Experience found, creator_id: {experience.user_id}")
        
        # Get the creator of the experience
        creator_id = experience.user_id
        
        # Skip match checking if the creator is the same as the current user
        if creator_id == current_user_id:
            print(f"DEBUG: User is the creator, skipping match")
            # Still record the swipe if needed
            if not UserSwipe.query.filter_by(user_id=current_user_id, experience_id=experience_id).first():
                new_swipe = UserSwipe(user_id=current_user_id, experience_id=experience_id, direction=is_like)
                db.session.add(new_swipe)
                db.session.commit()
                print(f"DEBUG: Created new swipe for user's own experience")
            return jsonify({
                'detail': 'Swipe recorded successfully',
                'match_created': False
            })
        
        # Check if the user has already swiped on this experience
        existing_swipe = UserSwipe.query.filter_by(
            user_id=current_user_id,
            experience_id=experience_id
        ).first()
        
        swipe_updated = False
        if existing_swipe:
            print(f"DEBUG: Found existing swipe: id={existing_swipe.id}, direction={existing_swipe.direction}")
            # If the swipe direction is different, update it
            if existing_swipe.direction != is_like:
                existing_swipe.direction = is_like
                db.session.commit()
                swipe_updated = True
                print(f"DEBUG: Updated existing swipe to direction={is_like}")
            elif not is_like:
                # If user is disliking again, just return
                return jsonify({'detail': 'Swipe already recorded', 'match_created': False}), 200
            # If user is liking again, continue to check for matches
        else:
            # Record new swipe
            new_swipe = UserSwipe(
                user_id=current_user_id,
                experience_id=experience_id,
                direction=is_like
            )
            db.session.add(new_swipe)
            db.session.commit()
            print(f"DEBUG: Created new swipe id={new_swipe.id}")
        
        # Invalidate the cached preference vector since the user has new swipe data
        try:
            user = User.query.get(current_user_id)
            if user and user.preference_vector and (not existing_swipe or swipe_updated):
                print(f"User {current_user_id}: Invalidating preference vector after new swipe")
                user.preference_vector_updated_at = datetime.utcnow()  # Keep the vector but mark it as needing update
                db.session.commit()
        except Exception as e:
            print(f"User {current_user_id}: Error updating preference vector timestamp: {e}")
            # Continue even if this fails
        
        # If user liked (swiped right), check for a match
        if is_like:
            print(f"DEBUG: User liked experience, checking for match. Creator_id: {creator_id}")
            
            # Check for existing match between these users for this experience
            existing_match = Match.query.filter(
                ((Match.user1_id == current_user_id) & (Match.user2_id == creator_id) |
                (Match.user1_id == creator_id) & (Match.user2_id == current_user_id)),
                Match.experience_id == experience_id
            ).first()
            
            if existing_match:
                print(f"DEBUG: Found existing match id={existing_match.id}, status={existing_match.status}")
                return jsonify({
                    'detail': 'Match already exists',
                    'match_created': False,
                    'match': {
                        'id': existing_match.id,
                        'status': existing_match.status,
                        'other_user': {
                            'id': creator_id,
                            'username': User.query.get(creator_id).name if User.query.get(creator_id) else 'Unknown'
                        }
                    }
                })
            
            # Create a pending match immediately when a user swipes right
            new_match = Match(
                user1_id=current_user_id,  # The user who swiped
                user2_id=creator_id,       # The creator of the experience
                experience_id=experience_id,
                status='pending'
            )
            db.session.add(new_match)
            db.session.commit()
            
            print(f"DEBUG: Match created id={new_match.id} between user {current_user_id} and user {creator_id} for experience {experience_id}")
            
            # Return success with match info
            return jsonify({
                'detail': 'Swipe recorded successfully',
                'match_created': True,
                'match': {
                    'id': new_match.id,
                    'other_user': {
                        'id': creator_id,
                        'username': User.query.get(creator_id).name if User.query.get(creator_id) else 'Unknown'
                    }
                }
            })
        
        # Return success without match
        print(f"DEBUG: Swipe recorded successfully, no match created (dislike or other reason)")
        return jsonify({
            'detail': 'Swipe recorded successfully',
            'match_created': False
        })
        
    except Exception as e:
        print(f"DEBUG: Error recording swipe: {e}")
        import traceback
        traceback.print_exc()  # Print full stack trace
        db.session.rollback()
        return jsonify({'detail': str(e)}), 500
    
@swipe_bp.route('/api/swipe-experiences', methods=['GET'])
@login_required()
def get_swipe_experiences(current_user_id=None):
    """
    Return personalized experiences for the swipe interface based on user preferences.
    
    This simplified endpoint uses Pinecone vector search to find experiences that match
    the user's preference vector based solely on experience type.
    
    After a user has swiped through all experiences, they will be shown again in the same order.
    """
    try:
        # Get the current user
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'detail': 'User not found'}), 404
        
        print(f"User {current_user_id}: Retrieving personalized swipe experiences")
        
        # Get experiences the user has already swiped on
        swiped_experience_ids = [
            swipe.experience_id for swipe in 
            UserSwipe.query.filter_by(user_id=current_user_id).all()
        ]
        print(f"User {current_user_id}: Has already swiped on {len(swiped_experience_ids)} experiences")
        
        # Get all experiences except user's own and filter out already swiped experiences
        all_experiences = Experience.query.filter(
            Experience.user_id != current_user_id,
            ~Experience.id.in_(swiped_experience_ids) if swiped_experience_ids else True
        ).all()
        
        print(f"User {current_user_id}: Found {len(all_experiences)} unswiped experiences")
        
        if len(all_experiences) == 0:
            print(f"User {current_user_id}: No unswiped experiences found")
            return jsonify([]), 200
        
        # Parse the user's experience_type preferences for direct matching and reason generation
        user_preferred_exp_types = []
        if user.experience_type_prefs:
            try:
                exp_prefs = json.loads(user.experience_type_prefs)
                if isinstance(exp_prefs, dict):
                    user_preferred_exp_types = [exp_type for exp_type, is_selected in exp_prefs.items() if is_selected]
                elif isinstance(exp_prefs, list):
                    user_preferred_exp_types = exp_prefs
            except:
                # Fallback for non-JSON format
                if isinstance(user.experience_type_prefs, str):
                    if ',' in user.experience_type_prefs:
                        user_preferred_exp_types = [x.strip() for x in user.experience_type_prefs.split(',') if x.strip()]
                    else:
                        user_preferred_exp_types = [user.experience_type_prefs.strip()]
        
        print(f"User {current_user_id} preferred experience types: {user_preferred_exp_types}")
            
        # Use Pinecone for vector similarity search if available
        if backend.recommender.pinecone_initialized and hasattr(user, 'preference_vector') and user.preference_vector:
            print(f"User {current_user_id}: Using personalized experiences API for vector similarity ranking")
            
            # Get personalized experiences using the simplified vector approach
            # Note: We'll still filter out swiped experiences later
            matches = get_personalized_experiences(user, top_k=100)  # Get more results
            
            # Initialize scored_experiences
            scored_experiences = []
            

            print(f"User {current_user_id}: Found {len(matches)} matches from vector similarity search")
            
            # Create a dictionary of experiences by ID for quick lookup
            experiences_dict = {exp.id: exp for exp in all_experiences}
            
            # Process matches to create ordered list of experiences
            ordered_experiences = []
            for match in matches:
                exp_id = match.get('id')
                # Only include experiences that haven't been swiped on
                if exp_id in experiences_dict:
                    exp = experiences_dict[exp_id]
                    
                    # Add match score and reason to the experience object
                    exp.match_score = match.get('score', 0.5)
                    
                    # Generate a simple match reason based on type match
                    if exp.experience_type in user_preferred_exp_types:
                        exp.match_reason = f"Matches your preference for {exp.experience_type} experiences"
                    else:
                        exp.match_reason = "Experience you might like"
                    
                    ordered_experiences.append(exp)
            
            # Use the ordered experiences from vector search
            experiences = ordered_experiences
            
            # If we didn't get all experiences from vector search, add any missing ones at the end
            missing_exp_ids = set(experiences_dict.keys()) - {exp.id for exp in ordered_experiences}
            if missing_exp_ids:
                print(f"User {current_user_id}: Adding {len(missing_exp_ids)} experiences not found in vector search")
                for exp_id in missing_exp_ids:
                    exp = experiences_dict[exp_id]
                    exp.match_score = 0.3  # Lower baseline score for non-vector matches
                    exp.match_reason = "Other experience you might like"
                    experiences.append(exp)
        else:
            # If vector ranking is not available, do basic preference matching on experience type only
            print(f"User {current_user_id}: No preference vector available, doing basic preference matching")
            
            # Score experiences based on direct preference matching
            scored_experiences = []
            for exp in all_experiences:
                # Starting score
                score = 0.5  # Neutral
                
                # Get the creator
                creator = User.query.get(exp.user_id)
                if not creator:
                    continue
                
                # Match on experience type preferences
                if exp.experience_type and user_preferred_exp_types:
                    if exp.experience_type in user_preferred_exp_types:
                        score += 0.3  # Strong boost for exact match
                    else:
                        # Check for partial matches
                        for preferred_type in user_preferred_exp_types:
                            if preferred_type.lower() in exp.experience_type.lower() or exp.experience_type.lower() in preferred_type.lower():
                                score += 0.2  # Moderate boost for partial match
                                break
                
                # Create match reason
                match_reason = "Experience you might like"
                if exp.experience_type and exp.experience_type in user_preferred_exp_types:
                    match_reason = f"Matches your preference for {exp.experience_type} experiences"
                
                scored_experiences.append({
                    'experience': exp,
                    'score': score,
                    'reason': match_reason
                })
            
            # Sort by score
            scored_experiences.sort(key=lambda x: x['score'], reverse=True)
            
            # Get sorted experiences
            experiences = [item['experience'] for item in scored_experiences]
            
            # Add match scores and reasons to the experiences
            for i, exp in enumerate(experiences):
                matching_item = next((item for item in scored_experiences if item['experience'].id == exp.id), None)
                if matching_item:
                    exp.match_score = matching_item['score']
                    exp.match_reason = matching_item['reason']
        
        print(f"User {current_user_id}: Preparing {len(experiences)} experiences for response")
        
        result = []
        for exp in experiences:
            # Get the creator of the experience
            creator = User.query.get(exp.user_id)
            
            # Skip if creator no longer exists (shouldn't happen but for safety)
            if not creator:
                print(f"User {current_user_id}: Skipping experience {exp.id} as creator no longer exists")
                continue
                
            # Clean up text data
            experience_type = exp.experience_type.strip() if exp.experience_type else ''
            location = exp.location.strip() if exp.location else ''
            description = exp.description.strip() if exp.description else ''
            
            # Prepare result with match score and reason if available
            exp_data = {
                'id': exp.id,
                'user_id': exp.user_id,
                'creator_name': creator.name if creator else 'Unknown',
                'creator_netid': creator.netid if creator else '',
                'creator_profile_image': creator.profile_image if creator else None,
                'creator_class_year': creator.class_year if creator else None,  # Add class year for UI display
                'creator_major': creator.major if creator else None,  # Add major for UI display
                'experience_type': experience_type,
                'location': location,
                'description': description,
                'latitude': exp.latitude,
                'longitude': exp.longitude,
                'place_id': exp.place_id,
                'location_image': exp.location_image,
                'created_at': exp.created_at.isoformat() if exp.created_at else None
            }
            
            # Add match score and reason if available
            if hasattr(exp, 'match_score'):
                exp_data['match_score'] = float(exp.match_score)  # Convert to float to ensure it's JSON serializable
                exp_data['match_reason'] = getattr(exp, 'match_reason', "Experience you might like")
            
            result.append(exp_data)
        
        print(f"User {current_user_id}: Returning {len(result)} experiences for swiping")
        return jsonify(result)
    except Exception as e:
        print(f"User {current_user_id}: Error fetching swipe experiences: {e}")
        import traceback
        traceback.print_exc()  # Print stack trace for better debugging
        return jsonify({'detail': str(e)}), 500

@swipe_bp.route('/swipe')
def serve_swipe():
    return current_app.send_static_file('index.html')