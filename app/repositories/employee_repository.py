from app.models.employee import Employee, EntryExit
from app import db
from datetime import date, timedelta, datetime

class EmployeeRepository:
    @staticmethod
    def add_employee(name):
        employee = Employee(name=name)
        db.session.add(employee)
        db.session.commit()

    @staticmethod
    def add_entry_exit(employee_id, action):
        entry_exit = EntryExit(employee_id=employee_id, action=action)
        db.session.add(entry_exit)
        db.session.commit()

    @staticmethod
    def get_entries_exits_by_date(specific_date=None):
        start_datetime = datetime.combine(specific_date, datetime.min.time())
        end_datetime = start_datetime + timedelta(days=1)
        
        # Query within the start and end of the specific_date
        return db.session.query(EntryExit).filter(
            EntryExit.timestamp >= start_datetime,
            EntryExit.timestamp < end_datetime
        ).all()
