import os
import sys

# Ensure the project root directory is in sys.path so 'app' module is discoverable
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app

# Vercel looks for the WSGI application instance named 'app'
app = create_app()

if __name__ == "__main__":
    app.run()
