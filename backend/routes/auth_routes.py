from flask import Blueprint, request, jsonify, current_app, session, redirect
from flask_cors import CORS
from functools import wraps
import os
import secrets
from urllib.parse import quote_plus, urlencode, quote

from ..utils.auth_utils import login_required, is_authenticated, get_cas_login_url, logout_cas, strip_ticket, _CAS_URL, validate

# Import database models
try:
    # Try local import first (for local development)
    from database import db, User, Experience, Match, UserSwipe, UserImage, add_new_columns, drop_unused_columns
    from backend.utils.recommender_utils import index_experience, get_personalized_experiences, get_embedding, get_user_preference_text, get_experience_text
    import backend.utils.recommender_utils as recommender_utils
except ImportError:
    # Fall back to package import (for Heroku)
    from backend.database import db, User, Experience, Match, UserSwipe, UserImage, add_new_columns, drop_unused_columns
    from backend.utils.recommender_utils import index_experience, get_personalized_experiences, get_embedding, get_user_preference_text, get_experience_text
    import backend.utils.recommender_utils

auth_bp = Blueprint('auth_routes', __name__)

@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.json
    
    # Check if username already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'detail': 'Username already exists'}), 400
    
    # Create new user
    new_user = User(
        username=data['username'],
        name=data['name'],
        gender=data['gender'],
        class_year=data['class_year'],
        interests=data['interests'],
        profile_image=data.get('profile_image')
    )
    new_user.set_password(data['password'])
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201
    
@auth_bp.route('/api/cas/login', methods=['GET'])
def cas_login():
    """Initiate CAS login process and return login URL"""
    try:
        callback_url = request.args.get('callback_url', '/')
        login_url = get_cas_login_url(callback_url)
        return jsonify({'login_url': login_url})
    except Exception as e:
        return jsonify({'detail': f'Error: {str(e)}'}), 500

@auth_bp.route('/api/cas/callback', methods=['GET'])
def cas_callback():
    """Process CAS authentication callback"""
    try:
        ticket = request.args.get('ticket')
        callback_url = request.args.get('callback_url', '/')
        
        # Determine the frontend URL based on environment
        # In production, the app is served from the same domain
        if 'herokuapp.com' in request.host or os.environ.get('PRODUCTION') == 'true':
            # In production, use the same host
            scheme = request.headers.get('X-Forwarded-Proto', 'https')
            frontend_url = f"{scheme}://{request.host}"
        else:
            # In development, get from Origin header or use localhost:3000 as fallback
            frontend_url = request.headers.get('Origin', 'http://localhost:3000')
        
        if not ticket:
            return jsonify({'detail': 'No ticket provided'}), 400
        
        # Step 1: Validate ticket with CAS server - Authentication happens first
        user_info = validate(ticket)
        
        if not user_info:
            return jsonify({'detail': 'Invalid CAS ticket'}), 401
        
        # Store user info in session
        session['user_info'] = user_info
        netid = user_info.get('user', '')
        
        # Extract attributes for more user information if available
        attributes = user_info.get('attributes', {})
        # Use principalId as the cas_id if available, otherwise use netid
        cas_id = attributes.get('principalId', netid)
        
        # Step 2: Check if user exists in our database - first by netid, then by cas_id
        user = User.query.filter_by(netid=netid).first()
        if not user:
            user = User.query.filter_by(cas_id=cas_id).first()
        
        is_new_user = False
        # If user doesn't exist, we'll create one with information from CAS
        if not user:
            is_new_user = True
            # Get display name or default to netID
            display_name = attributes.get('displayName', f"{netid.capitalize()} User")
            
            # Create a new user with the netid and cas_id
            new_user = User(
                username=netid,
                netid=netid,
                cas_id=cas_id,
                name=display_name,
                # Set optional fields to default values that can be updated later
                gender='Other',
                class_year=2025,
                interests='{"hiking": true, "dining": true, "movies": true, "study": true}',
                profile_image=f'https://ui-avatars.com/api/?name={netid}&background=orange&color=fff',
                password_hash=secrets.token_hex(16),
                onboarding_completed=False,  # Explicitly set onboarding as not completed for new users
                phone_number=attributes.get('phoneNumber', ''),
                preferred_email=attributes.get('email', '')
            )
            db.session.add(new_user)
            db.session.commit()
            
            # Retrieve the user after commit
            user = User.query.filter_by(netid=netid).first()
        elif not user.netid or not user.cas_id:
            # If we have a user but they're missing netid or cas_id, update them
            if not user.netid:
                user.netid = netid
            if not user.cas_id:
                user.cas_id = cas_id
            db.session.commit()
        
        # Step 3: Determine if onboarding is needed
        # New users ALWAYS need onboarding, existing users only if onboarding_completed is False
        needs_onboarding = is_new_user or not user.onboarding_completed
        print(f"User {user.username} is new: {is_new_user}, needs onboarding: {needs_onboarding}")
        
        # Step 4: Redirect based on authentication and onboarding status
        # For production environment (Heroku) - CRITICAL FIX: Always redirect to root with hash params to avoid 404s
        if 'herokuapp.com' in request.host or os.environ.get('PRODUCTION') == 'true':
            # In SPAs on Heroku, we need to redirect to the root and let React Router handle it
            redirect_url = f"{frontend_url}/#/cas/callback?callback_url={quote(callback_url)}&needs_onboarding={str(needs_onboarding).lower()}&cas_success=true"
            print(f"Redirecting to: {redirect_url}")
            return redirect(redirect_url)
        else:
            # In development, redirect to the React dev server
            redirect_url = f"{frontend_url}/cas/callback?callback_url={quote(callback_url)}&needs_onboarding={str(needs_onboarding).lower()}&cas_success=true"
            print(f"Redirecting to: {redirect_url}")
            return redirect(redirect_url)
            
    except Exception as e:
        print(f"Error in CAS callback: {e}")
        # Determine frontend URL for error redirect
        if 'herokuapp.com' in request.host or os.environ.get('PRODUCTION') == 'true':
            scheme = request.headers.get('X-Forwarded-Proto', 'https')
            frontend_url = f"{scheme}://{request.host}"
        else:
            frontend_url = request.headers.get('Origin', 'http://localhost:3000')
            
        # Include more detailed error information
        error_message = str(e)
        error_type = type(e).__name__
        
        # Redirect to login page with error message
        error_redirect = f"{frontend_url}/login?error={quote(f'Authentication failed ({error_type}): {error_message}')}"
        print(f"Redirecting to error URL: {error_redirect}")
        return redirect(error_redirect)

@auth_bp.route('/api/cas/logout', methods=['GET'])
def cas_logout():
    """Handle CAS logout"""
    try:
        # Clear session 
        session.clear()
        
        # Determine logout URL
        frontend_url = request.args.get('frontend_url', '')
        
        if not frontend_url:
            if 'herokuapp.com' in request.host or os.environ.get('PRODUCTION') == 'true':
                scheme = request.headers.get('X-Forwarded-Proto', 'https')
                frontend_url = f"{scheme}://{request.host}"
            else:
                frontend_url = request.headers.get('Origin', 'http://localhost:3000')
        
        # Add /login to the frontend URL to ensure redirection to login page
        login_url = f"{frontend_url}/login"
        print(f"Setting CAS logout service URL to: {login_url}")
        
        # Generate CAS logout URL with specific redirect to login page
        logout_url = f"{_CAS_URL}logout?service={quote(login_url)}"
        
        return jsonify({
            'message': 'Logged out successfully',
            'logout_url': logout_url
        })
    except Exception as e:
        print(f"Error in CAS logout: {e}")
        return jsonify({'detail': f'Error: {str(e)}'}), 500

@auth_bp.route('/api/cas/status', methods=['GET'])
def cas_status():
    """Check if the user is authenticated with CAS"""
    authenticated = is_authenticated()
    return jsonify({'authenticated': authenticated})

@auth_bp.route('/login')
def serve_login():
    return current_app.send_static_file('index.html')