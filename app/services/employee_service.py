from datetime import date
from app.repositories.employee_repository import EmployeeRepository

class EmployeeService:
    @staticmethod
    def track_entry_exit(employee_id, action):
        EmployeeRepository.add_entry_exit(employee_id, action)

    @staticmethod
    def get_daily_entries_exits():
        return EmployeeRepository.get_entries_exits_by_date(date.today())
