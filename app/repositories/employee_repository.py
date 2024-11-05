from app.models.employee import Employee, EntryExit
from app.data_base import db
from datetime import date, timedelta, datetime
import face_recognition

class EmployeeRepository:
    @staticmethod
    def add_employee(name, face_data):
        print('In repo layer')
        employee = Employee(empoyee_name=name, face_data=face_data)
        print('Inserting Employee data in DB')
        db.session.add(employee)
        db.session.commit()

    @staticmethod
    def get_employee_entry_exit_records(employee_id):
        print('In repo layer')
        employees = EntryExit.query.filter_by(employee_id=employee_id).all()
        employee_data = [employee.to_dict() for employee in employees]
        print('fetching Employee entry exit data in DB')
        return employee_data

    @staticmethod
    def add_entry_exit(employee_id, employee_name, cam_id, action):
        entry_exit = EntryExit(employee_id=employee_id, employee_name=employee_name, cam_id=cam_id, action=action)
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

    @staticmethod
    def find_by_face_data(face_encoding):
        print('In repo service to fetch face data by ID')
        employees = db.session.query(Employee).all()
        print(f'Fetched emplyees in DB {employees}')
        for employee in employees:
            print('Checking lits of employees fetched from DB')
            if face_recognition.compare_faces([employee.face_data], face_encoding)[0]:
                print('Employee matched')
                return employee
        return None
