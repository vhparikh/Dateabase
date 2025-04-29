from flask import Blueprint, request, jsonify, current_app, session, redirect
from flask_cors import CORS
from functools import wraps
from datetime import datetime, timedelta, timezone
import jwt
import os
import secrets
from urllib.parse import quote_plus, urlencode, quote

from .auth_utils import login_required, decode_token, is_authenticated
from .auth import validate, is_authenticated, get_cas_login_url, logout_cas, strip_ticket, _CAS_URL

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

@auth_bp.route('/api/token', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'detail': 'Please provide both username and password'}), 400
    
    try:
        # Find the user with the given username
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({'detail': 'Invalid username or password'}), 401
            
        access_token = jwt.encode({
            'sub': user.id,
            'username': user.username,
            'exp': datetime.now(timezone.utc) + timedelta(days=30)  # Extended token validity
        }, current_app.config['SECRET_KEY'], algorithm='HS256')
        
        refresh_token = jwt.encode({
            'sub': user.id,
            'exp': datetime.now(timezone.utc) + timedelta(days=90)  # Extended refresh token
        }, current_app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'access': access_token,
            'refresh': refresh_token
        })
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'detail': str(e)}), 500

@auth_bp.route('/api/token/refresh', methods=['POST'])
def refresh_token():
    refresh = request.json.get('refresh')
    
    try:
        # If no refresh token provided, check if user is authenticated via CAS session
        if not refresh:
            # Check if user is authenticated via CAS
            if not is_authenticated():
                return jsonify({'detail': 'Authentication required'}), 401
            
            user_info = session.get('user_info', {})
            netid = user_info.get('user', '')
            
            # Find the user by netid
            user = User.query.filter_by(netid=netid).first()
            if not user:
                return jsonify({'detail': 'User not found'}), 404
            
            # Generate new tokens
            access_token = jwt.encode({
                'sub': user.id,
                'username': user.username,
                'exp': datetime.now(timezone.utc) + timedelta(days=30)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')
            
            refresh_token = jwt.encode({
                'sub': user.id,
                'exp': datetime.now(timezone.utc) + timedelta(days=90)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')
            
            return jsonify({
                'access': access_token,
                'refresh': refresh_token
            })
        else:
            # Handle provided refresh token
            user_id = decode_token(refresh)
            if isinstance(user_id, str) and user_id.startswith('Invalid'):
                return jsonify({'detail': user_id}), 401
                
            user = User.query.get(user_id)
            if not user:
                return jsonify({'detail': 'User not found'}), 404
            
            access_token = jwt.encode({
                'sub': user.id,
                'username': user.username,
                'exp': datetime.now(timezone.utc) + timedelta(days=30)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')
            
            return jsonify({
                'access': access_token,
                'refresh': refresh  # Return the same refresh token
            })
    except Exception as e:
        print(f"Error in refresh_token: {e}")
        return jsonify({'detail': str(e)}), 500
    
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
        
        # Generate token for the frontend
        access_token = jwt.encode({
            'sub': user.id,
            'username': netid,
            'exp': datetime.now(timezone.utc) + timedelta(days=1)
        }, current_app.config['SECRET_KEY'], algorithm='HS256')
        
        refresh_token = jwt.encode({
            'sub': user.id,
            'exp': datetime.now(timezone.utc) + timedelta(days=30)
        }, current_app.config['SECRET_KEY'], algorithm='HS256')
        
        # Step 3: Determine if onboarding is needed
        # New users ALWAYS need onboarding, existing users only if onboarding_completed is False
        needs_onboarding = is_new_user or not user.onboarding_completed
        print(f"User {user.username} is new: {is_new_user}, needs onboarding: {needs_onboarding}")
        
        # Step 4: Redirect based on authentication and onboarding status
        # For production environment (Heroku) - CRITICAL FIX: Always redirect to root with hash params to avoid 404s
        if 'herokuapp.com' in request.host or os.environ.get('PRODUCTION') == 'true':
            # In SPAs on Heroku, we need to redirect to the root and let React Router handle it
            # Otherwise we get 404 errors when users don't have cookies
            print(f"Heroku environment detected, redirecting to root with appropriate hash")
            
            # Store auth tokens in secure HttpOnly cookies
            resp = None
            if needs_onboarding:
                # Send to root with #/onboarding hash for client-side routing
                resp = redirect(f"/?redirectTo=onboarding")
                print(f"Redirecting new user to onboarding")
            else:
                # For authenticated users with completed onboarding
                target = callback_url.lstrip('/') if callback_url != '/' else 'swipe'
                resp = redirect(f"/?redirectTo={target}")
                print(f"Redirecting authenticated user to {target}")
            
            # Set tokens in cookies for good measure
            resp.set_cookie('access_token', access_token, httponly=True, secure=True, max_age=86400)
            resp.set_cookie('refresh_token', refresh_token, httponly=True, secure=True, max_age=2592000)
            return resp
        
        # For local development - redirect directly to the route
        else:
            if needs_onboarding:
                print(f"Local dev: Redirecting to {frontend_url}/onboarding")
                return redirect(f"{frontend_url}/onboarding")
            else:
                target = f"{frontend_url}/{callback_url.lstrip('/')}" if callback_url != '/' else f"{frontend_url}/swipe"
                print(f"Local dev: Redirecting to {target}")
                return redirect(target)
    except Exception as e:
        print(f"CAS callback error: {str(e)}")
        return jsonify({'detail': f'Error: {str(e)}'}), 500

@auth_bp.route('/api/cas/logout', methods=['GET'])
def cas_logout():
    """Log out user from CAS"""
    # Clear the session
    session.clear()
    
    # Determine the frontend URL based on the environment
    if 'herokuapp.com' in request.host:
        # In production (Heroku), use the same host with https
        frontend_url = f"https://{request.host}"
    else:
        # In development, get from Origin header or use localhost:3000 as fallback
        frontend_url = request.headers.get('Origin', 'http://localhost:3000')
    
    # Redirect to the root URL after logout, let frontend handle the routing
    redirect_url = f"{frontend_url}/"
    logout_url = f"{_CAS_URL}logout?service={quote(redirect_url)}"
    
    # Return the logout URL to the frontend so it can redirect
    return jsonify({
        'detail': 'Logged out successfully',
        'logout_url': logout_url
    })

@auth_bp.route('/api/cas/status', methods=['GET'])
def cas_status():
    """Check if user is authenticated with CAS"""
    is_auth = is_authenticated()
    return jsonify({'authenticated': is_auth})

@auth_bp.route('/login')
def serve_login():
    return current_app.send_static_file('index.html')