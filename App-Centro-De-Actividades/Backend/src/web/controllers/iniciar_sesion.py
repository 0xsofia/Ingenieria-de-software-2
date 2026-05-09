from flask import Blueprint

login_bp = Blueprint("login", __name__, url_prefix="/api")


@login_bp.route("/login", methods=["GET", "POST"])
def index():
    return "tests"
