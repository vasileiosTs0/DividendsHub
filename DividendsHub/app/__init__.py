import dash
from flask import Flask
from flask.helpers import get_root_path
from flask_login import login_required
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from app.config import Config

#from app.extensions import db

#from config import BaseConfig


def create_app(config_class=Config):
    server = Flask(__name__)
    server.config.from_object(Config)

    
    register_extensions(server)
    register_blueprints(server)
    register_mail(server)

    from app import webapp
    #register_dashapps(server)

    return server


def register_dashapps(app):
    from app.dashapp1.layout import layout
    from app.dashapp1.callbacks import register_callbacks

    # Meta tags for viewport responsiveness
    meta_viewport = {"name": "viewport", "content": "width=device-width, initial-scale=1, shrink-to-fit=no"}
    external_stylesheets=["./assets/responsive-sidebar.css"]

    dashapp1 = dash.Dash(__name__,
                         server=app,
                         url_base_pathname='/dashboard/',
                         assets_folder=get_root_path(__name__) + '/assets/',
                         assets_external_path='./dashboard/assets',
                         external_stylesheets=external_stylesheets,
                         meta_tags=[meta_viewport])

    with app.app_context():
        dashapp1.title = 'Dashboard'
        dashapp1.layout = layout
        register_callbacks(dashapp1)
    _protect_dashviews(dashapp1)
    print(dashapp1.config.meta_tags)
    print(dashapp1.config.external_stylesheets)

def _protect_dashviews(dashapp):
    for view_func in dashapp.server.view_functions:
        if view_func.startswith(dashapp.config.url_base_pathname):
            dashapp.server.view_functions[view_func] = login_required(dashapp.server.view_functions[view_func])


def register_extensions(server):
    from app.extensions import db
    from app.extensions import login

    #from app.extensions import migrate

    from app.models import User
    db.init_app(server)
    with server.app_context():
        db.create_all()
    
    login.init_app(server)
    login.login_view = 'main.login'
    login.login_message_category = 'info'
    #migrate.init_app(server, db)
    return db


def register_mail(server):
    from app.extensions import mail

    mail = Mail(server)
    
    return mail


def register_blueprints(server):
    from app.webapp import server_bp

    server.register_blueprint(server_bp)