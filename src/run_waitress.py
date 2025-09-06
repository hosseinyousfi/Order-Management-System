#!/usr/bin/env python
import os, sys

# Ensure project root is on sys.path and cwd
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
os.chdir(BASE_DIR)

# Django & Waitress imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
from django.core.wsgi import get_wsgi_application
from waitress import serve

application = get_wsgi_application()

if __name__ == "__main__":
    serve(application, host='0.0.0.0', port=8000)
