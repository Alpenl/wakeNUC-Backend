from flask import Blueprint

api = Blueprint('openid_v3', __name__, url_prefix='/v3')

from .getopenid import *
