import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///employee_tracking.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
