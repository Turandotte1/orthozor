#! encoding: utf-8
#! python3

from flask import Blueprint
questionnaire = Blueprint('questionnaire', __name__)
from . import routes