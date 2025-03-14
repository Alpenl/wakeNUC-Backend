from flask import Blueprint

api = Blueprint('physical_v3', __name__, url_prefix='/v3')

from .physical import *
