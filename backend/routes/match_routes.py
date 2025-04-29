from flask import Blueprint, jsonify, current_app
from ..database import Match, User, Experience, db
from ..utils.auth_utils import login_required
from ..utils.match_utils import get_match_reason

match_bp = Blueprint('match_routes', __name__)

@match_bp.route('/api/matches/<int:user_id>', methods=['GET'])
def get_matches(user_id):
    try:
        print(f"DEBUG: get_matches called for user_id: {user_id}")
        
        # Get both confirmed and pending matches for this user
        all_matches = Match.query.filter(
            (Match.user1_id == user_id) | (Match.user2_id == user_id)
        ).all()
        
        print(f"DEBUG: Found {len(all_matches)} total matches for user_id: {user_id}")
        
        # Use sets to track which combinations we've already processed to avoid duplicates
        processed_combinations = set()
        
        confirmed_matches = []
        pending_received = []  # Matches where user is the experience owner and needs to accept
        pending_sent = []      # Matches where user liked someone else's experience
        
        for match in all_matches:
            # Determine the other user in the match
            other_user_id = match.user2_id if match.user1_id == user_id else match.user1_id
            other_user = User.query.get(other_user_id)
            experience = Experience.query.get(match.experience_id)
            
            print(f"DEBUG: Processing match_id: {match.id}, status: {match.status}, experience_id: {match.experience_id}")
            print(f"DEBUG: Match is between user1_id: {match.user1_id} and user2_id: {match.user2_id}")
            
            if not other_user or not experience:
                print(f"DEBUG: Skipping match_id: {match.id} - missing other_user or experience")
                continue
            
            # Create a unique key for this match combination to avoid duplicates
            # We sort the user IDs to ensure (user1, user2) and (user2, user1) create the same key
            match_key = (min(user_id, other_user_id), max(user_id, other_user_id), experience.id)
            
            # Skip if we've already processed this combination
            if match_key in processed_combinations:
                print(f"DEBUG: Skipping duplicate match combination: {match_key}")
                continue
                
            # Add to processed set
            processed_combinations.add(match_key)
            
            print(f"DEBUG: Experience owner_id: {experience.user_id}")
            
            match_data = {
                'match_id': match.id,
                'other_user': {
                    'id': other_user.id,
                    'name': other_user.name,
                    'gender': other_user.gender,
                    'class_year': other_user.class_year,
                    'profile_image': other_user.profile_image if hasattr(other_user, 'profile_image') else None
                },
                'experience': {
                    'id': experience.id,
                    'experience_type': experience.experience_type,
                    'location': experience.location,
                    'description': experience.description,
                    'latitude': experience.latitude,
                    'longitude': experience.longitude,
                    'place_id': experience.place_id,
                    'location_image': experience.location_image,
                    'owner_id': experience.user_id
                },
                'created_at': match.created_at.isoformat() if match.created_at else None,
                'status': match.status
            }
            
            # Categorize the match
            if match.status == 'confirmed':
                print(f"DEBUG: Match {match.id} is confirmed - adding to confirmed_matches")
                confirmed_matches.append(match_data)
            elif match.status == 'pending':
                # If user is the experience owner, they need to accept/reject
                if experience.user_id == user_id:
                    print(f"DEBUG: Match {match.id} is pending and user is experience owner - adding to pending_received")
                    pending_received.append(match_data)
                else:
                    # User sent the like
                    print(f"DEBUG: Match {match.id} is pending and user is not experience owner - adding to pending_sent")
                    pending_sent.append(match_data)
            
            print(f"DEBUG: categorized match {match.id} correctly")
        
        print(f"DEBUG: Returning {len(confirmed_matches)} confirmed, {len(pending_received)} pending_received, {len(pending_sent)} pending_sent matches")
        
        # Return categorized matches
        result = {
            'confirmed': confirmed_matches,
            'pending_received': pending_received,
            'pending_sent': pending_sent
        }
        
        print(f"DEBUG: Final match counts - confirmed: {len(confirmed_matches)}, pending_received: {len(pending_received)}, pending_sent: {len(pending_sent)}")
        return jsonify(result)
    except Exception as e:
        print(f"ERROR: Error fetching matches: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
@match_bp.route('/api/matches/<int:match_id>/accept', methods=['PUT'])
@login_required()
def accept_match(match_id, current_user_id=None):
    try:
        # Get the match
        match = Match.query.get(match_id)
        if not match:
            return jsonify({'detail': 'Match not found'}), 404
            
        # Get the experience to verify ownership
        experience = Experience.query.get(match.experience_id)
        if not experience:
            return jsonify({'detail': 'Experience not found'}), 404
            
        # Verify that the current user is either involved in the match as user1 or user2
        if current_user_id != match.user1_id and current_user_id != match.user2_id:
            return jsonify({'detail': 'You are not authorized to interact with this match'}), 403
        
        # If the user is the experience owner, they can confirm the match
        if experience.user_id == current_user_id:
            # Update match status to confirmed
            match.status = 'confirmed'
            db.session.commit()
            
            return jsonify({
                'message': 'Match accepted successfully', 
                'match': {
                    'id': match.id,
                    'status': match.status,
                    'experience_id': match.experience_id
                }
            }), 200
        else:
            return jsonify({'detail': 'Only the experience owner can accept a match'}), 403
    except Exception as e:
        print(f"Error accepting match: {e}")
        db.session.rollback()
        return jsonify({'detail': str(e)}), 500

@match_bp.route('/api/matches/<int:match_id>/reject', methods=['PUT'])
@login_required()
def reject_match(match_id, current_user_id=None):
    try:
        # Get the match
        match = Match.query.get(match_id)
        if not match:
            return jsonify({'detail': 'Match not found'}), 404
            
        # Get the experience to verify ownership
        experience = Experience.query.get(match.experience_id)
        if not experience:
            return jsonify({'detail': 'Experience not found'}), 404
            
        # Verify that the current user is either involved in the match as user1 or user2
        if current_user_id != match.user1_id and current_user_id != match.user2_id:
            return jsonify({'detail': 'You are not authorized to interact with this match'}), 403
        
        # Any user involved in the match can reject it
        # Delete the match
        db.session.delete(match)
        db.session.commit()
        
        return jsonify({'message': 'Match rejected successfully'}), 200
    except Exception as e:
        print(f"Error rejecting match: {e}")
        db.session.rollback()
        return jsonify({'detail': str(e)}), 500
    
@match_bp.route('/matches')
def serve_matches():
    return current_app.send_static_file('index.html')