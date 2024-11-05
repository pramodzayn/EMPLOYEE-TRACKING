from datetime import datetime
from app.data_base import db

class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    empoyee_name = db.Column(db.String(50), nullable=False)
    face_data = db.Column(db.PickleType, nullable=False)
    entries_exits = db.relationship('EntryExit', back_populates='employee', cascade="all, delete-orphan")

class EntryExit(db.Model):
    __tablename__ = 'entries_exits'
    id = db.Column(db.Integer, primary_key=True)
    cam_id = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    action = db.Column(db.String(10), nullable=False)  # 'entry' or 'exit'
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    employee_name = db.Column(db.String(50), nullable=True, default="Unknown")
    employee = db.relationship('Employee', back_populates='entries_exits')

    def to_dict(self):
        return {
            "id": self.id,
            "cam_id": self.cam_id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "employee_id": self.employee_id,
            "employee_name": self.employee_name
        }
