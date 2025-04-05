# error_handler.py
from flask import jsonify
import traceback
import logging

# Logger setup
logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base class for API exceptions"""
    def __init__(self, message, status_code=500, payload=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        result = dict(self.payload or {})
        result['error'] = self.message
        return result


class ScrapingError(APIError):
    """Scraping-related errors"""
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=400, payload=payload)


class AnalysisError(APIError):
    """Analysis-related errors"""
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=500, payload=payload)


class ValidationError(APIError):
    """Input validation errors"""
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=400, payload=payload)


class ExternalAPIError(APIError):
    """External API call errors"""
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=502, payload=payload)


def register_error_handlers(app):
    """Register error handlers for the Flask app"""
    
    @app.errorhandler(404)
    def not_found(e):
        """Handle access to non-existent endpoints"""
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        """Handle disallowed HTTP methods"""
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(APIError)
    def handle_api_error(e):
        """Handle APIError and its subclasses"""
        response = jsonify(e.to_dict())
        response.status_code = e.status_code
        logger.error(f"API Error: {e.message} (Code: {e.status_code})")
        return response

    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        """Handle all other exceptions"""
        error_trace = traceback.format_exc()
        logger.error(f"Unhandled Exception: {str(e)}\n{error_trace}")
        
        # Hide detailed error information in production
        response = jsonify({
            "error": "An internal server error occurred",
            "error_id": str(hash(str(e)))[:8]  # ID for error tracking
        })
        response.status_code = 500
        return response