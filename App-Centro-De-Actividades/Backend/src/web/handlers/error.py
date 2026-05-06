from dataclasses import dataclass
from flask import render_template


@dataclass
class Error:
    code : int
    message: str
    description : str

def not_found_error(e):
    error = Error(404,"Ups! No pudimos encontrar lo que estás buscando",
                  "La URL que estás buscando no se encuentra en nuestro servidor")
    return render_template("error.html",error= error),404