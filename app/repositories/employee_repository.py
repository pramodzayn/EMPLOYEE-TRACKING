from app.models.employee import Employee, EntryExit
from app.data_base import db
from datetime import date, timedelta, datetime
import face_recognition
import pickle
import pytz
import numpy as np
from scipy.spatial.distance import cosine

class EmployeeRepository:
    @staticmethod
    def add_employee(name, face_data):
        print('In repo layer')
        employee = Employee(employee_name=name, face_data=face_data)
        print('Inserting Employee data in DB')
        db.session.add(employee)
        db.session.commit()

    @staticmethod
    def get_employee_entry_exit_records(employee_name):
        print('In repo layer')
        employees = EntryExit.query.filter_by(employee_name=employee_name).all()
        employee_data = [employee.to_dict() for employee in employees]
        print('fetching Employee entry exit data in DB')
        return employee_data

    @staticmethod
    def add_entry_exit(employee_id, employee_name, cam_id, action):
        central = pytz.timezone('America/Chicago')
        central_time = datetime.now(central)
        entry_exit = EntryExit(employee_id=employee_id, employee_name=employee_name, timestamp=central_time, cam_id=cam_id, action=action)
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
            stored_face_encoding = pickle.loads(employee.face_data)
            print('Deserialized data fetched from DB')
            if stored_face_encoding is None:
                    print(f"[Warning] Stored face encoding for employee {employee.id} is None. Skipping.")
                    continue
            if not isinstance(stored_face_encoding, np.ndarray):
                stored_face_encoding = np.array(stored_face_encoding)
            if not isinstance(face_encoding, np.ndarray):
                face_encoding = np.array(face_encoding)
            
            # Calculate cosine similarity
            similarity = 1 - cosine(stored_face_encoding, face_encoding)
            print(f"Cosine similarity with employee {employee.id}: {similarity:.4f}")
            
            # Set a similarity threshold (e.g., 0.9)
            if similarity > 0.9:
                print('Employee matched!')
                return employee
        #     if face_recognition.compare_faces([stored_face_encoding], face_encoding)[0]:
        #         print('Employee matched')
        #         return employee
        # print("No matching employee found.")
        return None
