#!encoding: utf-8
#!python 3

import os
from app import create_app



app = create_app(os.getenv('FLASK_CONFIG') or 'default')
