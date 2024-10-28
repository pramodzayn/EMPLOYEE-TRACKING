from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    from app.views.employee_view import employee_view
    app.register_blueprint(employee_view, url_prefix='/api')

    return app
