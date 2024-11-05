from flask import Blueprint, request, jsonify
from app.services.employee_service import EmployeeService
from app.services.face_recognition_service import FaceRecognitionService
from app.repositories.employee_repository import EmployeeRepository

employee_view = Blueprint('employee_view', __name__)

@employee_view.route('/getEmployeeHistory', methods=['GET'])
def get_employee_entry_exit_records():
    data = request.json
    employee_id = data.get('employee_id')
    record = EmployeeService.get_employee_entry_exit_records(employee_id)
    return jsonify(record), 200

@employee_view.route('/entries_exits', methods=['GET'])
def get_entries_exits():
    date = request.args.get('date')
    entries_exits = EmployeeService.get_daily_entries_exits(date)
    return jsonify([entry.serialize() for entry in entries_exits]), 200

@employee_view.route('/addEmployee', methods=['POST'])
def add_employee():
    data = request.json
    name = data.get('name')
    if name is None:
        return jsonify({"status": "error", "message": "Employee name is required"}), 400
    # Capture image from the webcam
    print(f'EmployeeName is : {name}')
    image = FaceRecognitionService.capture_employee_image()
    if image is None:
        return jsonify({"error": "Failed to capture image"}), 500
    print('Face image is captured')
    EmployeeService.add_employee(name, image)
    print('Saved successfully')
    return jsonify({"status": "success", "message": f"Employee {name} added successfully"})
