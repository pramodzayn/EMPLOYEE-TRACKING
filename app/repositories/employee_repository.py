from app.models.employee import Employee, EntryExit
from app.data_base import db
from datetime import date, timedelta, datetime
import face_recognition
import pickle
import pytz
import numpy as np
from scipy.spatial.distance import cosine
from openpyxl import Workbook
from openpyxl.drawing.image import Image
import os

class EmployeeRepository:
    # Directory to temporarily save frames as images
    
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
    def add_entry_exit(employee_id, employee_name, cam_id, action, frame):
        central = pytz.timezone('America/Chicago')
        central_time = datetime.now(central)
        entry_exit = EntryExit(employee_id=employee_id, employee_name=employee_name, timestamp=central_time, cam_id=cam_id, action=action, frame_data=pickle.dumps(frame))
        db.session.add(entry_exit)
        db.session.commit()

    @staticmethod
    def get_entries_exits_by_date(specific_date=None):
        TEMP_FRAME_DIR = "temp_frames"

        if not os.path.exists(TEMP_FRAME_DIR):
            os.makedirs(TEMP_FRAME_DIR)

        start_datetime = datetime.combine(specific_date, datetime.min.time())
        end_datetime = start_datetime + timedelta(days=1)
        
        # Query within the start and end of the specific_date
        entries = db.session.query(EntryExit).filter(
            EntryExit.timestamp >= start_datetime,
            EntryExit.timestamp < end_datetime
        ).all()
        wb = Workbook()
        ws = wb.active
        ws.title = "Entries Exits"
        
        # Header row
        headers = ["ID", "Employee ID", "Employee Name", "Camera ID", "Action", "Timestamp", "Captured Face"]
        ws.append(headers)
        for row_idx, entry in enumerate(entries, start=2):
            frame_file = None
            if entry.frame_data:
                try:
                    # Deserialize frame and save it temporarily
                    frame = pickle.loads(entry.frame_data)
                    frame_file = os.path.join(TEMP_FRAME_DIR, f"frame_{entry.id}.jpg")
                    cv2.imwrite(frame_file, frame)

                    # Resize the image to fit into the Excel cell if needed
                    image = cv2.imread(frame_file)
                    if image.shape[1] > 200 or image.shape[0] > 200:  # Limit to 200x200
                        resized_image = cv2.resize(image, (200, 200), interpolation=cv2.INTER_AREA)
                        cv2.imwrite(frame_file, resized_image)
                except Exception as e:
                    print(f"[Error] Could not process frame for entry ID {entry.id}: {e}")
                    frame_file = None

            # Append data to the Excel sheet
            ws.append([
                entry.id,
                entry.employee_id,
                entry.employee_name,
                entry.camera_id,
                entry.action,
                entry.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                "Frame embedded below" if frame_file else "No Frame"
            ])

            # Embed the frame into the Excel sheet
            if frame_file:
                img = Image(frame_file)
                img.width, img.height = 100, 100  # Adjust image size in the cell
                ws.add_image(img, f"G{row_idx}")  # Column "G" for frames

        # Save the Excel file
        excel_filename = f"daily_report_{date.today()}.xlsx"
        wb.save(excel_filename)
        print(f"Excel sheet with embedded frames generated: {excel_filename}")
        # Clean up temporary frame files
        for file in os.listdir(TEMP_FRAME_DIR):
            os.remove(os.path.join(TEMP_FRAME_DIR, file))
        os.rmdir(TEMP_FRAME_DIR)
        
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
