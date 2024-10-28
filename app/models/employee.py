from datetime import datetime
from app import db

class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    entries_exits = db.relationship('EntryExit', back_populates='employee', cascade="all, delete-orphan")

class EntryExit(db.Model):
    __tablename__ = 'entries_exits'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    action = db.Column(db.String(10), nullable=False)  # 'entry' or 'exit'
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    employee = db.relationship('Employee', back_populates='entries_exits')
