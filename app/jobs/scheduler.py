from apscheduler.schedulers.background import BackgroundScheduler
from app.services.employee_service import EmployeeService
from app.services.face_recognition_service import FaceRecognitionService
from app.utils.spreadsheet_export import export_to_spreadsheet
import cv2
import threading
from app.jobs.camera_urls import camera_urls

def scheduled_task(app):
    with app.app_context():
        data = EmployeeService.get_daily_entries_exits()
        export_to_spreadsheet(data)

def start_webcam_monitoring(app, cam_id):
    def webcam_capture():
        with app.app_context():
            video_capture = cv2.VideoCapture(0) # Use the system's main webcam (camera index 0)
            if not video_capture.isOpened():
                print(f"Failed to open the webcam with cam_id {cam_id}.")
                return
            print('capturing the cam')
            while video_capture.isOpened():
                print('Video capture is opened')
                ret, frame = video_capture.read()
                if not ret:
                    print(f"Failed to capture frame from the webcam {cam_id}")
                    break

                print('captured the imahe ret is not null')
                # Process the frame using face recognition
                FaceRecognitionService.process_camera_feed(frame, cam_id)

            video_capture.release()
    # Start the webcam capture in a separate thread
    capture_thread = threading.Thread(target=webcam_capture, daemon=True)
    capture_thread.start()

def init_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=lambda: scheduled_task(app), trigger='interval', hours=24)
    scheduler.start()

    #camera_url = "http://your_camera_url"
    cam_id = "local_cam"  # Unique identifier for each camera
    capture_thread = threading.Thread(target=start_webcam_monitoring(app, cam_id), daemon=True)
    #capture_thread.daemon = True  # Ensure thread closes when main program exits
    capture_thread.start()