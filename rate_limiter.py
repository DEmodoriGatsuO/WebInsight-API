# rate_limiter.py
from flask import request, jsonify
import time
from functools import wraps
import threading
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter implementation"""
    
    def __init__(self, limit=10, window=60):
        """
        Args:
            limit (int): Maximum number of requests within time window
            window (int): Time window in seconds
        """
        self.limit = limit
        self.window = window
        self.clients = {}
        self.lock = threading.Lock()
        
        # Start a thread to periodically clean up old client information
        self._start_cleanup_thread()
        
    def _start_cleanup_thread(self):
        """Start a thread to clean up expired client entries"""
        def cleanup():
            while True:
                time.sleep(self.window)
                self._cleanup_old_entries()
                
        cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        cleanup_thread.start()
        
    def _cleanup_old_entries(self):
        """Remove expired entries"""
        with self.lock:
            current_time = time.time()
            to_delete = []
            
            for client_id, entries in self.clients.items():
                # Remove expired requests
                self.clients[client_id] = [e for e in entries if current_time - e < self.window]
                
                # Mark empty client entries for deletion
                if not self.clients[client_id]:
                    to_delete.append(client_id)
            
            # Remove empty client entries
            for client_id in to_delete:
                del self.clients[client_id]
    
    def is_rate_limited(self, client_id):
        """Check if a client has reached the rate limit"""
        with self.lock:
            current_time = time.time()
            
            # Create new entry for client if it doesn't exist
            if client_id not in self.clients:
                self.clients[client_id] = []
            
            # Remove expired requests
            self.clients[client_id] = [t for t in self.clients[client_id] if current_time - t < self.window]
            
            # Check if request count exceeds limit
            if len(self.clients[client_id]) >= self.limit:
                return True
                
            # Add new request
            self.clients[client_id].append(current_time)
            return False


def rate_limit(limiter, get_client_id=lambda: request.remote_addr):
    """
    Decorator to apply rate limiting to Flask routes
    
    Args:
        limiter: RateLimiter instance
        get_client_id: Function to get client identifier
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            client_id = get_client_id()
            
            if limiter.is_rate_limited(client_id):
                logger.warning(f"Rate limit exceeded for client: {client_id}")
                response = jsonify({
                    "error": "Rate limit exceeded. Please try again later.",
                    "rate_limit": {
                        "limit": limiter.limit,
                        "window": limiter.window,
                        "unit": "seconds"
                    }
                })
                response.status_code = 429
                return response
                
            return f(*args, **kwargs)
        return wrapped
    return decorator


# Usage example:
"""
from rate_limiter import RateLimiter, rate_limit

# Set up rate limiter
api_limiter = RateLimiter(limit=10, window=60)  # 10 requests per minute

@app.route('/api/endpoint', methods=['POST'])
@rate_limit(api_limiter)
def api_endpoint():
    # Implementation...
"""