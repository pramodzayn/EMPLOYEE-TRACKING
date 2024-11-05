import pandas as pd
from datetime import date

def export_to_spreadsheet(data):
    rows = [{ "Employee ID": entry.employee_id, "Employee Name": entry.employee_name, "Timestamp": entry.timestamp, "Action": entry.action, "Cam_ID": entry.cam_id } for entry in data]
    df = pd.DataFrame(rows)
    filename = f"S:\OwnProjects\employee-tracking\daily_report_{date.today()}.xlsx"
    df.to_excel(filename, index=False)
    print(f"Report saved to {filename}")
