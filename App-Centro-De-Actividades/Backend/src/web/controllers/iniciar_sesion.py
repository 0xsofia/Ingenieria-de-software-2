from flask import Blueprint

login_bp = Blueprint("auths", __name__, url_prefix="/auths")


@login_bp.route("/login", methods=["GET", "POST"])
def index(): ...
