from datetime import date
from app.repositories.employee_repository import EmployeeRepository

class EmployeeService:
    @staticmethod
    def get_employee_entry_exit_records(employee_name):
        return EmployeeRepository.get_employee_entry_exit_records(employee_name)

    @staticmethod
    def get_daily_entries_exits(date):
        EmployeeRepository.get_entries_exits_by_date(date)

    @staticmethod
    def add_employee(name, face_encoding):
        print('In service layer')
        return EmployeeRepository.add_employee(name, face_encoding)
