#! encoding: utf-8
#! python3

from . import routes
from flask import Blueprint
auth = Blueprint('auth', __name__)
