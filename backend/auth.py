"""
auth.py
CAS Authentication for Dateabase application
"""

import urllib.parse
import re
import json
import flask
import requests
from flask import session, request, redirect, url_for, abort, current_app

_CAS_URL = 'https://fed.princeton.edu/cas/'

# Return url after stripping out the "ticket" parameter that was
# added by the CAS server.
def strip_ticket(url):
    if url is None:
        return "something is badly wrong"
    url = re.sub(r'ticket=[^&]*&?', '', url)
    url = re.sub(r'\?&?$|&$', '', url)
    return url

# Validate a login ticket by contacting the CAS server. If
# valid, return the user's user_info; otherwise, return None.
def validate(ticket):
    """Validate a login ticket by contacting the CAS server"""
    try:
        # Princeton CAS requires that the service URL in validation EXACTLY matches 
        # the one used during login, including all query parameters in the same order
        
        # Extract current host and protocol
        if 'herokuapp.com' in flask.request.host:
            scheme = 'https'  # Force HTTPS for Heroku
        else:
            scheme = 'http'   # Use HTTP for local development
        
        host = flask.request.host
        callback_url = flask.request.args.get('callback_url', '/')
        
        # Reconstruct the exact service URL used for CAS login
        service_url = f"{scheme}://{host}/api/cas/callback"
        
        # Always include the callback_url parameter in the same format
        # This must match exactly what we sent during login
        service_url += f"?callback_url={urllib.parse.quote(callback_url)}"
        
        # Princeton CAS is extremely strict - adding or removing any parameter will cause validation to fail
        print(f"CAS validation using service URL: {service_url}")
        
        # Build the validation URL
        val_url = (_CAS_URL + "validate"
            + '?service=' + urllib.parse.quote(service_url)
            + '&ticket=' + urllib.parse.quote(ticket)
            + '&format=json')
        
        print(f"CAS validation URL: {val_url}")
        
        # Make the validation request
        response = requests.get(val_url, verify=False)
        if response.status_code != 200:
            print('CAS validation failed with status code:', response.status_code)
            return None
            
        result = response.json()
        
        if (not result) or ('serviceResponse' not in result):
            return None

        service_response = result['serviceResponse']

        if 'authenticationSuccess' in service_response:
            user_info = service_response['authenticationSuccess']
            return user_info

        if 'authenticationFailure' in service_response:
            print('CAS authentication failure:', service_response)
            return None

        print('Unexpected CAS response:', service_response)
        return None
    except Exception as e:
        print('Error validating CAS ticket:', str(e))
        return None

# Authenticate the user, and return the user's info.
# Do not return unless the user is successfully authenticated.
def authenticate():
    # If the user_info is in the session, then the user was
    # authenticated previously. So return the user_info.
    if 'user_info' in flask.session:
        user_info = flask.session.get('user_info')
        return user_info

    # If the request does not contain a login ticket, then redirect
    # the browser to the login page to get one.
    ticket = flask.request.args.get('ticket')
    if ticket is None:
        login_url = (_CAS_URL + 'login?service=' +
            urllib.parse.quote(flask.request.url))
        flask.abort(flask.redirect(login_url))

    # If the login ticket is invalid, then redirect the browser
    # to the login page to get a new one.
    user_info = validate(ticket)
    if user_info is None:
        login_url = (_CAS_URL + 'login?service='
            + urllib.parse.quote(strip_ticket(flask.request.url)))
        flask.abort(flask.redirect(login_url))

    # The user is authenticated, so store the user_info in
    # the session and return the user_info.
    flask.session['user_info'] = user_info
    return user_info

def is_authenticated():
    return 'user_info' in flask.session

def logout_cas():
    # Log out of the CAS session
    logout_url = (_CAS_URL + 'logout?service='
        + urllib.parse.quote(request.url_root))
    return redirect(logout_url)

def get_cas_login_url(callback_url=None):
    """Get the CAS login URL for the frontend to redirect to"""
    if callback_url is None:
        callback_url = request.args.get('callback_url', request.referrer or '/')
    
    # Determine service URL based on environment
    if 'herokuapp.com' in request.host:
        # In Heroku, we'll use the app's domain
        scheme = request.headers.get('X-Forwarded-Proto', 'https')
        host = request.host
        
        # Our callback endpoint is /api/cas/callback on the backend
        # But the frontend at /cas/callback will redirect to this
        api_callback = f"{scheme}://{host}/api/cas/callback?callback_url={urllib.parse.quote(callback_url)}"
        
        print(f"Heroku CAS login service URL: {api_callback}")
    else:
        # In local development
        base_url = request.url_root.rstrip('/')
        api_callback = f"{base_url}/api/cas/callback?callback_url={urllib.parse.quote(callback_url)}"
        print(f"Local CAS login service URL: {api_callback}")
    
    # Generate the CAS login URL
    login_url = f"{_CAS_URL}login?service={urllib.parse.quote(api_callback)}"
    print(f"Final CAS login URL: {login_url}")
    
    return login_url
