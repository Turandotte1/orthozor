#! encoding: utf-8
#! python3

from flask import Blueprint
admin = Blueprint('admin', __name__)
from . import routes