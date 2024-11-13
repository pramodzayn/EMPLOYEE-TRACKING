from apscheduler.schedulers.background import BackgroundScheduler
from app.services.employee_service import EmployeeService
from app.services.face_recognition_service import FaceRecognitionService
from app.utils.spreadsheet_export import export_to_spreadsheet
import cv2
import threading
from app.jobs.camera_urls import camera_urls
from app.services.ffmpeg_utils import capture_frame_from_url
import time
from datetime import date
import imageio
import numpy as np
import face_recognition
import ffmpeg

def scheduled_task(app):
    with app.app_context():
        data = EmployeeService.get_daily_entries_exits(date.today())
        export_to_spreadsheet(data)

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

def process_rtsp_stream_with_ffmpeg(app, cam_id, rtsp_url, width=1280, height=720):
    with app.app_context():
        try:
            """Continuously captures frames from an RTSP stream and performs face detection."""
            process = (
                ffmpeg
                .input(rtsp_url, rtsp_transport='tcp')  # Set RTSP transport to TCP for stability
                .output('pipe:', format='rawvideo', pix_fmt='bgr24')
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )
            print('Processed rtsp url')
            while True:
                print('Reading rtsp url')
                in_bytes = process.stdout.read(width * height * 3)
                print('Width and height adjusted')
                if not in_bytes:
                    print("No more frames or stream has ended.")
                    break

                # Convert bytes to a numpy array and reshape for OpenCV
                frame = np.frombuffer(in_bytes, np.uint8).reshape([height, width, 3])
                print('frame shapped')
                FaceRecognitionService.process_camera_feed(frame, cam_id)
                
                # # Detect faces in the frame
                # face_locations = face_recognition.face_locations(bgr_frame)

                # if face_locations:
                #     print(f"Detected {len(face_locations)} face(s) in the frame.")
                # else:
                #     print("No faces detected.")
        except Exception as e:
                print(f'Failed in RTSP stream with ffmpeh: {e}')
        finally:
            print("RTSP stream reader is Null")
            process.stdout.close()
            process.wait()
            print("RTSP stream process closed.")

def start_all_cameras(app, camera_urls):
    for i, cam_url in enumerate(camera_urls, start=1):
        cam_id = f"camera_{i}"
        capture_thread = threading.Thread(target=process_camera_feed, args=(app, cam_id, cam_url), daemon=True)
        daemon=True #Ensures thread closes when main program exits
        capture_thread.start()

def init_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=lambda: scheduled_task(app), trigger='interval', hours=24)
    scheduler.start()
