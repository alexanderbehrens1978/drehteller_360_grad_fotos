from flask import Blueprint

sensors_bp = Blueprint('sensors', __name__, url_prefix='/sensors')

from . import routes
