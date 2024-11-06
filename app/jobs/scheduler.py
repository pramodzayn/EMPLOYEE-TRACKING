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

def start_webcam_monitoring(app, cam_id, cam_url):
    def webcam_capture():
        with app.app_context():
            video_capture = cv2.VideoCapture(cam_url) # Use the system's main webcam (camera index 0)
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

                print('captured the image ret is not null')
                # Process the frame using face recognition
                FaceRecognitionService.process_camera_feed(frame, cam_id)

            video_capture.release()
    # Start the webcam capture in a separate thread
    capture_thread = threading.Thread(target=webcam_capture, daemon=True)
    capture_thread.start()

def start_all_cameras(app, camera_urls):
    for i, cam_url in enumerate(camera_urls, start=1):
        cam_id = f"camera_{i}"
        capture_thread = threading.Thread(target=start_webcam_monitoring, args=(app, cam_id, cam_url), daemon=True)
        # daemon=True Ensures thread closes when main program exits
        capture_thread.start()

def init_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=lambda: scheduled_task(app), trigger='interval', hours=24)
    scheduler.start()

    # use below code for testing through local system cam to detect the entry exit action
    # cam_id = "local_cam"
    # cam_url = 0
    # capture_thread = threading.Thread(target=start_webcam_monitoring(app, cam_id, cam_url), daemon=True)
    # #capture_thread.daemon = True  # Ensure thread closes when main program exits
    # capture_thread.start()
