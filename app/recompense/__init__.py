#! encoding: utf-8
#! python3

from flask import Blueprint
recompense = Blueprint('recompense', __name__)
from . import routes