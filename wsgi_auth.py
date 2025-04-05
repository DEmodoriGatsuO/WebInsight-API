# wsgi_auth.py - Alternative WSGI Authentication Middleware Implementation
import os
import base64
import hmac
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get authentication information from environment variables
API_KEY = os.environ.get('API_KEY')
API_KEYS = os.environ.get('API_KEYS', '').split(',') if os.environ.get('API_KEYS') else []
BASIC_AUTH_USERNAME = os.environ.get('BASIC_AUTH_USERNAME')
BASIC_AUTH_PASSWORD = os.environ.get('BASIC_AUTH_PASSWORD')

# Import Flask application
from app import app as flask_app

class AuthMiddleware:
    """WSGI Authentication Middleware - Supports API key and Basic authentication"""
    
    def __init__(self, app):
        self.app = app
        
    def __call__(self, environ, start_response):
        # Get request path
        path = environ.get('PATH_INFO', '')
        
        # Only check API endpoints (excluding health check)
        if path.startswith('/api/') and path != '/api/health':
            # API key authentication check
            api_key = None
            
            # Get API key from header
            if 'HTTP_X_API_KEY' in environ:
                api_key = environ['HTTP_X_API_KEY']
            
            # Get API key from query parameter
            if not api_key and 'QUERY_STRING' in environ:
                query = environ['QUERY_STRING']
                if 'api_key=' in query:
                    import urllib.parse
                    params = urllib.parse.parse_qs(query)
                    if 'api_key' in params:
                        api_key = params['api_key'][0]
            
            # Check API key
            if api_key:
                if API_KEY and hmac.compare_digest(api_key, API_KEY):
                    # API key is valid - continue with request
                    return self.app(environ, start_response)
                    
                # Check multiple API keys
                for valid_key in API_KEYS:
                    if valid_key and hmac.compare_digest(api_key, valid_key):
                        # API key is valid - continue with request
                        return self.app(environ, start_response)
            
            # Basic authentication check
            if BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD:
                if 'HTTP_AUTHORIZATION' in environ:
                    auth = environ['HTTP_AUTHORIZATION']
                    if auth.startswith('Basic '):
                        try:
                            auth_decoded = base64.b64decode(auth[6:]).decode('utf-8')
                            user, passwd = auth_decoded.split(':', 1)
                            if user == BASIC_AUTH_USERNAME and hmac.compare_digest(passwd, BASIC_AUTH_PASSWORD):
                                # Basic authentication is valid - continue with request
                                return self.app(environ, start_response)
                        except Exception:
                            pass
            
            # Authentication failed
            if BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD:
                # Prompt for Basic authentication
                start_response('401 Unauthorized', [
                    ('Content-Type', 'text/plain'),
                    ('WWW-Authenticate', 'Basic realm="WebInsight API"')
                ])
                return [b'Basic authentication is required']
            else:
                # API key authentication failed
                start_response('403 Forbidden', [('Content-Type', 'application/json')])
                return [b'{"error": "Access denied. Valid API key required."}']
        
        # Non-API request or authentication successful - continue with normal application processing
        return self.app(environ, start_response)

# Wrap Flask app with middleware
app = AuthMiddleware(flask_app)

# WSGI application used by PythonAnywhere
# If using this file, specify it in the PythonAnywhere WSGI configuration