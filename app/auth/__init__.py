#! encoding: utf-8
#! python3

from flask import Blueprint
auth = Blueprint('auth', __name__)
from . import routes