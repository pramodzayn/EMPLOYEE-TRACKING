from apscheduler.schedulers.background import BackgroundScheduler
from app.services.employee_service import EmployeeService
from app.utils.spreadsheet_export import export_to_spreadsheet

def scheduled_task(app):
    with app.app_context():
        data = EmployeeService.get_daily_entries_exits()
        export_to_spreadsheet(data)

def init_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=lambda: scheduled_task(app), trigger='interval', minutes=1)
    return scheduler
