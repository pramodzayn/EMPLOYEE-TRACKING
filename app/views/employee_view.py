from flask import Blueprint, request, jsonify, render_template
from app.services.employee_service import EmployeeService
from app.services.face_recognition_service import FaceRecognitionService
from app.repositories.employee_repository import EmployeeRepository
import pickle
import face_recognition

employee_view = Blueprint('employee_view', __name__)

@employee_view.route('/')
def index():
    return render_template('index.html')

@employee_view.route('/getEmployeePage')
def getEmployeeDashboard():
    return render_template('getEmployee.html')

@employee_view.route('/getEmployeeHistory', methods=['GET'])
def get_employee_entry_exit_records():
    data = request.json
    employee_name = data.get('employee_name')
    record = EmployeeService.get_employee_entry_exit_records(employee_name)
    return jsonify(record), 200

@employee_view.route('/entries_exits', methods=['GET'])
def get_entries_exits():
    date = request.args.get('date')
    entries_exits = EmployeeService.get_daily_entries_exits(date)
    return jsonify([entry.serialize() for entry in entries_exits]), 200

@employee_view.route('/addEmployee', methods=['POST'])
def add_employee():
    fname = request.form.get('firstName')
    lname = request.form.get('lastName')
    name = fname+' '+lname
    image_file = request.files.get('picture')
    if name is None:
        return jsonify({"status": "error", "message": "Employee name is required"}), 400
    print(f'EmployeeName is : {name}')
    if image_file is None:
        return jsonify({"status": "error", "message": "Image is required"}), 400

    # Convert the uploaded image to a face encoding
    image = face_recognition.load_image_file(image_file)
    face_encodings = face_recognition.face_encodings(image)
    if face_encodings:
        face_encoding = face_encodings[0]  # Use the first face found
    else:
        face_encoding = None
    # face_encoding = FaceRecognitionService.encode_face(image_file)
    # Serialize the face encoding for storage
    face_encoding_binary = pickle.dumps(face_encoding)
    EmployeeService.add_employee(name, face_encoding_binary)
    print('Saved successfully')
    return jsonify({"status": "success", "message": f"Employee {name} added successfully"})
