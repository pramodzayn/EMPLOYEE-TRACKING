from flask import Blueprint, request, jsonify
from app.services.employee_service import EmployeeService
from app.repositories.employee_repository import EmployeeRepository

employee_view = Blueprint('employee_view', __name__)

@employee_view.route('/track', methods=['POST'])
def track_entry_exit():
    data = request.json
    employee_id = data.get('employee_id')
    action = data.get('action')
    EmployeeService.track_entry_exit(employee_id, action)
    return jsonify({"status": "success", "message": f"{action} recorded successfully"})

@employee_view.route('/employee', methods=['POST'])
def add_employee():
    data = request.json
    name = data.get('name')
    if name:
        EmployeeRepository.add_employee(name)
        return jsonify({"status": "success", "message": f"Employee {name} added successfully"})
    else:
        return jsonify({"status": "error", "message": "Employee name is required"}), 400

