from apscheduler.schedulers.background import BackgroundScheduler
from app.services.employee_service import EmployeeService
from app.services.face_recognition_service import FaceRecognitionService
from app.utils.spreadsheet_export import export_to_spreadsheet
import cv2
import threading
from app.jobs.camera_urls import camera_urls
from app.services.ffmpeg_utils import capture_frame_from_url
import time

def scheduled_task(app):
    with app.app_context():
        data = EmployeeService.get_daily_entries_exits()
        export_to_spreadsheet(data)

def start_webcam_monitoring(app, cam_id, cam_url):
    def webcam_capture():
        with app.app_context():
            video_capture = cv2.VideoCapture(cam_url) # Use the system's main webcam (camera index 0)
            retry_attempts = 3  # Number of retry attempts
            retry_delay = 5  # Seconds to wait before retrying
            while True:
                if not video_capture.isOpened():
                    for attempt in range(retry_attempts):
                        print(f"Retry {attempt + 1} for {cam_id}:{cam_url}.")
                        video_capture.open(cam_url)
                        time.sleep(retry_delay)
                        if video_capture.isOpened():
                            print(f"Connection re-established for {cam_id}:{cam_url}.")
                            break
                    else:
                        print(f"Failed to reconnect to {cam_id}:{cam_url}. Skipping...")
                        return
                print(f"Connection established for {cam_id}:{cam_url}.")
                ret, frame = video_capture.read()
                if not ret:
                    print(f"Failed to capture frame from {cam_id}:{cam_url}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue

                FaceRecognitionService.process_camera_feed(frame, cam_id)

            video_capture.release()
    # Start the webcam capture in a separate thread
    capture_thread = threading.Thread(target=webcam_capture, daemon=True)
    capture_thread.start()

def initialize_camera(cam_url, cam_id):
    """Initialize camera connection."""
    video_capture = cv2.VideoCapture(cam_url)
    if not video_capture.isOpened():
        print(f"Failed to open camera with cam_id {cam_id}. Retrying...")
        retry_attempts = 3
        retry_delay = 5  # Seconds
        for attempt in range(retry_attempts):
            print(f"Retry {attempt + 1} for cam_id {cam_id}.")
            video_capture.open(cam_url)
            time.sleep(retry_delay)
            if video_capture.isOpened():
                print(f"Connection re-established for cam_id {cam_id}.")
                break
        else:
            print(f"Failed to connect to cam_id {cam_id} after multiple attempts.")
            return None
    return video_capture

def process_camera_feed(app, cam_id, cam_url):
    with app.app_context():  
        video_capture = initialize_camera(cam_url, cam_id)
        if video_capture is None:
            print("Exiting process due to camera initialization failure.")
            return

        print(f'Started monitoring camera: {cam_id} at {cam_url}')
        try:
            while True:
                print(f'Attempting to read camera: {cam_id} at {cam_url}')
                ret, frame = video_capture.read()
                print(f'Done frame capture reed for camera: {cam_id} at {cam_url}')
                if not ret:
                    print(f"Failed to capture frame from camera {cam_id}. Retrying...")
                    continue  # Exit loop and reconnect

                # Process the frame using face recognition
                FaceRecognitionService.process_camera_feed(frame, cam_id)
            
        except Exception as e:
            print(f"Error processing camera {cam_id}: {e}")

        finally:
            video_capture.release()  # Ensure the camera is released
            print(f"Stopped monitoring camera: {cam_id}. Retrying in 5 seconds...")
        
        # Reconnect after a short delay
        time.sleep(5)

def start_one_camera(app, cam_url):
    cam_id = "cam_1"
    process_camera_feed(app, cam_id, cam_url)

def start_all_cameras(app, camera_urls):
    # threads = []
    for i, cam_url in enumerate(camera_urls, start=1):
        cam_id = f"camera_{i}"
        #start_webcam_monitoring(app, cam_id, cam_url)
        capture_thread = threading.Thread(target=process_camera_feed, args=(app, cam_id, cam_url), daemon=True)
        daemon=True #Ensures thread closes when main program exits
        capture_thread.start()
        # threads.append(capture_thread)

    # Ensure that the main thread waits for all camera threads to finish
    # for thread in threads:
    #     thread.join()

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
