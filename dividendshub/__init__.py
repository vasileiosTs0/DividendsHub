import dash
from flask import Flask
from flask.helpers import get_root_path
from flask_login import login_required
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from dividendshub.config import Config


def create_app(config_class=Config):
    server = Flask(__name__)
    server.config.from_object(Config)

    register_extensions(server)
    register_blueprints(server)
    register_mail(server)

    from dividendshub import webapp
    # register_dashapps(server)

    return server


def _protect_dashviews(dashapp):
    for view_func in dashapp.server.view_functions:
        if view_func.startswith(dashapp.config.url_base_pathname):
            dashapp.server.view_functions[view_func] = login_required(dashapp.server.view_functions[view_func])


def register_extensions(server):
    from dividendshub.extensions import db
    from dividendshub.extensions import login

    # from dividendshub.extensions import migrate

    from dividendshub.models import User
    db.init_app(server)
    with server.app_context():
        db.create_all()

    login.init_app(server)
    login.login_view = 'main.login'
    login.login_message_category = 'info'
    # migrate.init_app(server, db)
    return db


def register_mail(server):
    from dividendshub.extensions import mail

    mail = Mail(server)

    return mail


def register_blueprints(server):
    from dividendshub.webapp import server_bp

    server.register_blueprint(server_bp)
