from flask import Flask
from app.config import Config
from app.data_base import init_db
from app.views.employee_view import employee_view
from app.jobs.scheduler import init_scheduler, start_all_cameras
from app.jobs.camera_urls import camera_urls
from threading import Thread
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    # Initialize database
    init_db(app)

    # Register app and adding prefix for endpoint url
    app.register_blueprint(employee_view, url_prefix='/api')

    # Intialize the scheduler to trigger the job
    init_scheduler(app)

    # Start all cameras in a background thread
    def start_camera_thread():
        start_all_cameras(app, camera_urls)
    
    start_camera_thread()
    return app
