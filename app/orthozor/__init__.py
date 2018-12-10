#! encodeing: utf-8
#! python3


from flask import Blueprint

orthozor = Blueprint('orthozor', __name__)
from . import routes