import dash
from flask import Flask
from flask.helpers import get_root_path
from flask_login import login_required
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from app.config import Config


def create_app(config_class=Config):
    server = Flask(__name__)
    server.config.from_object(Config)

    
    register_extensions(server)
    register_blueprints(server)
    register_mail(server)

    from app import webapp

    return server


def register_extensions(server):
    from app.extensions import db
    from app.extensions import login


    from app.models import User
    db.init_app(server)
    with server.app_context():
        db.create_all()
    
    login.init_app(server)
    login.login_view = 'main.login'
    login.login_message_category = 'info'
    return db


def register_mail(server):
    from app.extensions import mail

    mail = Mail(server)
    
    return mail


def register_blueprints(server):
    from app.webapp import server_bp

    server.register_blueprint(server_bp)