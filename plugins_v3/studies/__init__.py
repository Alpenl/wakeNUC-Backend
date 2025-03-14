from flask import Blueprint

api = Blueprint('studies_v3', __name__, url_prefix='/v3')

from .studies import *
