import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/FlaskApp/")
sys.path.insert(0,"/var/www/FlaskApp/FlaskApp/venv/lib/python3.8/site-packages/")

from FlaskApp import app as application
application.secret_key = 'asddi8fpobnasinhdoitSS'
