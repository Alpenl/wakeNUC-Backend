from flask import Blueprint

api = Blueprint('experiment_v3', __name__, url_prefix='/v3')

from .experiment import *
