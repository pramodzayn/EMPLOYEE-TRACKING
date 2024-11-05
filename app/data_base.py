from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()  # Ensure tables are created.
        print('Tables are created')
        print(f"Database path: {os.path.abspath('employee_tracking.db')}")