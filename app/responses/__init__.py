from flask import Blueprint
from . import server

blueprint = Blueprint('responses', __name__)
server.register_routes(blueprint)
