from app import create_app, db
from app.jobs.scheduler import init_scheduler
import os

app = create_app()
scheduler_init = init_scheduler(app)
scheduler_init.start()

with app.app_context():
    db.create_all()  # Ensure tables are created.
    print('Tables are created')
    print(f"Database path: {os.path.abspath('employee_tracking.db')}")

if __name__ == "__main__":
    app.run(debug=True)
