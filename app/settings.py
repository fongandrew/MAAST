"""
Use this for app wide settings.
"""
import os
import logging

# Root directory for GAE app
APP_ROOT = os.path.dirname(__file__)

# URL or relative path to static files
# If this is changed, remember to change app.yaml as well
STATIC_URL = STATIC_DIR = '/static'

# Where templates are located
TEMPLATES_DIR = os.path.join(APP_ROOT, 'templates')

# Name of site
SITE_NAME = 'Delorean Mail'

# Are we in debug mode?
DEBUG = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

# API Key and Secret for Context.IO
API_KEY = 'not_my_key'
API_SECRET = 'not_the_actual_secret'

# How many messages to fetch per match?
BATCH_LIMIT = 1000
# And if the above is too many, what's a smaller goal?
SMALLER_BATCH_LIMIT = 100
# How many times should we attempt to retry a message
# meta fetching task? Make sure queue.yaml is updated
# appropriately as well.
MAX_RETRIES = 10

# Number of contacts to prerender
NUM_CONTACTS = 10

# Settings for visualizations
NUM_FIRST_PHOTOS = 3
NUM_LAST_PHOTOS = 3
TOP_CC_COUNT = 5
TOP_TOPICS = 50
MAX_AWESOME = 5

# Default photo for contacts listing
DEFAULT_PHOTO = STATIC_URL + '/img/contact_thumb/NoPhoto.gif'

try:
    from locals import *
except ImportError:
    logging.warning("Unable to import local versions "
                    "of settings; using defaults")

# Constants in this file to make available to every template
TEMPLATE_CONSTANTS = [
    'SITE_NAME',
    'STATIC_DIR',
    'DEBUG'
]

# User name and API key for Tagul API
TAGUL_USER_NAME = '---'
TAGUL_API_KEY = '---'
