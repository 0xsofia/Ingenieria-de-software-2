from flask import Blueprint


session_bp = Blueprint('auths',__name__,url_prefix='/auths')

@session_bp.route("/",methods=['GET','POST'])
def index():
    ...
    
@session_bp.get("/logout")
def logout():
    ...
