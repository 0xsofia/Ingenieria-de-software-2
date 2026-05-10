from pathlib import Path

import click
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from sqlalchemy import text

db = SQLAlchemy()


def init_app(app):
    """Inicializar la base de datos."""
    db.init_app(app)
    config(app)

    return app


def config(app):
    """Cerrar la session de la base de datos al finalizar el contexto de la app"""

    @app.teardown_appcontext
    def close_session(exception=None):
        db.session.close()

    return app


def reset():
    """Recrea el schema local y aplica todas las migraciones."""
    alembic_config = _get_alembic_config()
    _ensure_single_head(alembic_config, "reset-db")

    click.echo("Eliminando schema public...")
    db.session.remove()

    with db.engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))

    click.echo("Aplicando migraciones hasta head...")
    command.upgrade(alembic_config, "head")
    click.echo("Finalizacion del reset de la base de datos!")


def ensure_seed_prerequisites():
    """Verifica que la base ya haya sido preparada antes de correr seeds."""
    required_tables = {
        "persona",
        "rol",
        "permiso",
        "persona_rol_puente",
        "rol_permiso_puente",
    }
    existing_tables = set(inspect(db.engine).get_table_names())

    if not required_tables.issubset(existing_tables):
        raise click.ClickException(
            "La base de datos no esta preparada para correr seeds. "
            "Primero ejecuta `flask reset-db` para crear el schema y aplicar las migraciones, "
            "y despues corre `flask seed_db`."
        )


def _ensure_single_head(alembic_config, command_name):
    heads = ScriptDirectory.from_config(alembic_config).get_heads()

    if len(heads) > 1:
        raise click.ClickException(
            "Se detectaron multiples heads de Alembic. "
            "Primero ejecuta `poetry run alembic heads`, luego resuelvelo con "
            "`poetry run alembic merge heads -m \"merge migration heads\"` y "
            f"finalmente corre de nuevo `flask {command_name}`."
        )


def _get_alembic_config():
    backend_root = Path(__file__).resolve().parents[2]
    alembic_ini_path = backend_root / "alembic.ini"
    alembic_config = Config(str(alembic_ini_path))
    alembic_config.set_main_option("script_location", str(backend_root / "alembic"))
    return alembic_config


def init():
    """Inicializa la base de datos"""
