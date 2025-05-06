from flask import Blueprint, request, jsonify, current_app, session, redirect
from flask_cors import CORS
from functools import wraps
import os
import secrets
from urllib.parse import quote_plus, urlencode, quote

from ..utils.auth_utils import login_required, is_authenticated, get_cas_login_url, logout_cas, strip_ticket, _CAS_URL, validate

    
from ..database import db, User, Experience, Match, UserSwipe, UserImage
from ..utils.recommender_utils import index_experience, get_personalized_experiences, get_embedding, get_user_preference_text, get_experience_text
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
        
        
        scheme = request.headers.get('X-Forwarded-Proto', 'https')
        frontend_url = f"{scheme}://{request.host}"
        
        if not ticket:
            return jsonify({'detail': 'No ticket provided'}), 400
        
        # Validate ticket with CAS server
        user_info = validate(ticket)
        
        if not user_info:
            return jsonify({'detail': 'Invalid CAS ticket'}), 401
        
        # Store user info in session
        session['user_info'] = user_info
        netid = user_info.get('user', '')
        
        # Check if user exists in our database
        user = User.query.filter_by(netid=netid).first()
        
        is_new_user = False
        
        if not user:
            is_new_user = True

            # Get attributes from user_info instead of using undefined variable
            attributes = user_info.get('attributes', {})
            display_name = attributes.get('displayName', f"{netid.capitalize()} User")
            
            # Create a new user
            new_user = User(
                username=netid,
                netid=netid,
                name=display_name,
                gender='Other',
                class_year=2025,
                interests='{"hiking": true, "dining": true, "movies": true, "study": true}',
                profile_image=f'https://ui-avatars.com/api/?name={netid}&background=orange&color=fff',
                password_hash=secrets.token_hex(16),
                onboarding_completed=False,
                phone_number=attributes.get('phoneNumber', ''),
                preferred_email=attributes.get('email', '')
            )
            db.session.add(new_user)
            db.session.commit()
            
            # Retrieve the user after commit
            user = User.query.filter_by(netid=netid).first()
        elif not user.netid:
            # If we have a user but they're missing netid, update them
            user.netid = netid
            db.session.commit()
        
        # Determine if onboarding is needed
        needs_onboarding = is_new_user or not user.onboarding_completed
        print(f"User {user.username} is new: {is_new_user}, needs onboarding: {needs_onboarding}")
        
        # Redirect based on authentication and onboarding status - fix by removing hash symbol
        redirect_url = f"{frontend_url}/#/cas/callback?callback_url={quote(callback_url)}&needs_onboarding={str(needs_onboarding).lower()}&cas_success=true"
        print(f"Redirecting to: {redirect_url}")
        return redirect(redirect_url)
            
    except Exception as e:
        print(f"Error in CAS callback: {e}")
        scheme = request.headers.get('X-Forwarded-Proto', 'https')
        frontend_url = f"{scheme}://{request.host}"
            
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
            scheme = request.headers.get('X-Forwarded-Proto', 'https')
            frontend_url = f"{scheme}://{request.host}"
        
        # Add /login to the frontend URL
        login_url = f"{frontend_url}/login"
        print(f"Setting CAS logout service URL to: {login_url}")
        
        # Generate CAS logout URL
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