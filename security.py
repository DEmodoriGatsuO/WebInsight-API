import os
import secrets
from functools import wraps
from flask import request, jsonify, Response
import logging
import hmac
import hashlib
import time

# Logger setup
logger = logging.getLogger(__name__)

# Get authentication information from environment variables
API_KEY = os.environ.get('API_KEY')
API_KEYS = os.environ.get('API_KEYS', '').split(',') if os.environ.get('API_KEYS') else []
BASIC_AUTH_USERNAME = os.environ.get('BASIC_AUTH_USERNAME')
BASIC_AUTH_PASSWORD = os.environ.get('BASIC_AUTH_PASSWORD')

# Warning log if API key is not set
if not API_KEY and not API_KEYS:
    logger.warning("API authentication is not configured. Please set the API_KEY or API_KEYS environment variable.")

# Warning log if Basic auth credentials are not set
if not BASIC_AUTH_USERNAME or not BASIC_AUTH_PASSWORD:
    logger.warning("Basic authentication is not configured. Please set the BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD environment variables.")

def generate_api_key():
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)

def check_api_key(api_key):
    """Check if the API key is valid"""
    if not api_key:
        return False
        
    # Check master API key
    if API_KEY and hmac.compare_digest(api_key, API_KEY):
        return True
        
    # Check multiple API keys
    for valid_key in API_KEYS:
        if valid_key and hmac.compare_digest(api_key, valid_key):
            return True
            
    return False

def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from header or query parameter
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        # Validate API key
        if not check_api_key(api_key):
            logger.warning(f"Access attempt with invalid API key: {request.remote_addr}")
            return jsonify({'error': 'Access denied. Valid API key required.'}), 403
        
        logger.debug(f"Access with valid API key: {request.remote_addr}")
        return f(*args, **kwargs)
    return decorated_function

def require_basic_auth(f):
    """Decorator to require Basic authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        
        # Validate credentials
        if not auth or auth.username != BASIC_AUTH_USERNAME or not hmac.compare_digest(auth.password, BASIC_AUTH_PASSWORD):
            logger.warning(f"Basic authentication failed: {request.remote_addr}")
            return Response(
                'Basic authentication required', 
                401, 
                {'WWW-Authenticate': 'Basic realm="WebInsight API"'}
            )
        
        logger.debug(f"Basic authentication successful: {request.remote_addr}")
        return f(*args, **kwargs)
    return decorated_function

def require_auth(f):
    """Decorator to require either API key or Basic authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check API key authentication
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        if check_api_key(api_key):
            return f(*args, **kwargs)
            
        # Check Basic authentication
        auth = request.authorization
        if BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD and auth and \
           auth.username == BASIC_AUTH_USERNAME and hmac.compare_digest(auth.password, BASIC_AUTH_PASSWORD):
            return f(*args, **kwargs)
            
        # Authentication failed
        logger.warning(f"Authentication failed: {request.remote_addr}")
        
        # Prompt for Basic authentication
        if BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD:
            return Response(
                'Basic authentication or API key required', 
                401, 
                {'WWW-Authenticate': 'Basic realm="WebInsight API"'}
            )
        else:
            return jsonify({'error': 'Access denied. Valid API key required.'}), 403
            
    return decorated_function

def setup_security(app):
    """Apply security settings to the application"""
    
    # Apply authentication to all API endpoints
    @app.before_request
    def authenticate():
        # Only check API endpoints
        if request.path.startswith('/api/') and request.path != '/api/health':
            # Check API key authentication
            api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
            if check_api_key(api_key):
                return None
                
            # Check Basic authentication
            auth = request.authorization
            if BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD and auth and \
               auth.username == BASIC_AUTH_USERNAME and hmac.compare_digest(auth.password, BASIC_AUTH_PASSWORD):
                return None
                
            # Authentication failed
            logger.warning(f"API authentication failed: {request.remote_addr} - {request.path}")
            
            # Prompt for Basic authentication
            if BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD:
                return Response(
                    'Basic authentication or API key required', 
                    401, 
                    {'WWW-Authenticate': 'Basic realm="WebInsight API"'}
                )
            else:
                return jsonify({'error': 'Access denied. Valid API key required.'}), 403

    # Startup information for administrators
    if not API_KEY and not API_KEYS:
        new_api_key = generate_api_key()
        logger.info(f"Security warning: API key is not set. It is recommended to set the following key as the API_KEY environment variable: {new_api_key}")
        
    return app