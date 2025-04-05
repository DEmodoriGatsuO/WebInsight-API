# wsgi.py
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Flask application
from app import app as flask_app

# Application used by PythonAnywhere
app = flask_app