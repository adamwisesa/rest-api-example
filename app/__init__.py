import os
from flask import Flask
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_assets import Environment
from flask_wtf import CsrfProtect
from flask_compress import Compress
from flask_rq import RQ
from flask_oauthlib.provider import OAuth2Provider
from flask_wtf import CsrfProtect
from flask_restful import Api

from config import config
from .assets import app_css, app_js, vendor_css, vendor_js

basedir = os.path.abspath(os.path.dirname(__file__))

mail = Mail()
db = SQLAlchemy()
csrf = CsrfProtect()
compress = Compress()
csrf = CsrfProtect()
oauth = OAuth2Provider()

# Set up Flask-Login
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'account.login'


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # not using sqlalchemy event system, hence disabling it

    config[config_name].init_app(app)

    # Set up extensions
    mail.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    compress.init_app(app)
    csrf.init_app(app)
    oauth.init_app(app)
    RQ(app)
    api = Api(app)

    # Register Jinja template functions
    from .utils import register_template_utils
    register_template_utils(app)

    # Set up asset pipeline
    assets_env = Environment(app)
    dirs = ['assets/styles', 'assets/scripts']
    for path in dirs:
        assets_env.append_path(os.path.join(basedir, path))
    assets_env.url_expire = True

    assets_env.register('app_css', app_css)
    assets_env.register('app_js', app_js)
    assets_env.register('vendor_css', vendor_css)
    assets_env.register('vendor_js', vendor_js)

    # Configure SSL if platform supports it
    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask_sslify import SSLify
        SSLify(app)

    # Create app blueprints
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .account import account as account_blueprint
    app.register_blueprint(account_blueprint, url_prefix='/account')

    from .api.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    from app.api.docs import docs as docs_blueprint
    app.register_blueprint(docs_blueprint)

    from flasgger import APISpec, Schema, Swagger, fields

    spec = APISpec(
        title='REST API',
        version='1.0.0',
        plugins=[
            'apispec.ext.flask',
            'apispec.ext.marshmallow',
        ],
    )

    app.config['SWAGGER'] = {
            'title': 'REST API',
            'uiversion': 3
    }

    swagger = Swagger(
            app,
            template={
                'swagger': '3.0',
                'info':
                {
                    'title': 'REST API',
                    'version': '1.0'
                }
            }
    )

    from app.api.v1.building import Building, BuildingList

    building_view = Building.as_view('Building')
    app.add_url_rule('/v1/buildings/<int:building_id>', view_func=building_view)

    building_list_view = BuildingList.as_view('BuildingList')
    app.add_url_rule('/v1/buildings', view_func=building_list_view)

    with app.test_request_context():
        spec.add_path(view=building_view)
        spec.add_path(view=building_list_view)

    return app
