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

def process_rtsp_stream_with_ffmpeg(app, cam_id, rtsp_url):
    with app.app_context():
        reader =  None
        try:
            # Use imageio with FFmpeg to read the RTSP stream
            reader = imageio.get_reader(rtsp_url, 'ffmpeg')
            print(f'connected to {rtsp_url} with imageio ffmpeg')
            while True:
                try:
                    # Grab the next frame from the stream
                    frame = reader.get_next_data()  # Manually fetch the next frame
                    print('Frame fetched')

                    # Convert the frame to a numpy array for OpenCV compatibility
                    frame = np.array(frame)
                    print('converted frame to array')

                    FaceRecognitionService.process_camera_feed(frame, cam_id)
                    # # Detect faces in the frame
                    # face_locations = face_recognition.face_locations(bgr_frame)

                    # if face_locations:
                    #     print(f"Detected {len(face_locations)} face(s) in the frame.")
                    # else:
                    #     print("No faces detected.")

                except (IndexError, RuntimeError) as frame_error:
                    # Handle frame retrieval errors
                    print(f"Frame retrieval error: {frame_error}")
                    break  # Break the loop if there's an issue with frame retrieval   
        except Exception as e:
            print(f'Failed in RTSP stream with imageio ffmpeh: {e}')
        finally:
            if reader is not None:
                reader.close()
                print("RTSP stream reader closed.")
            else:
                print("RTSP stream reader is Null")

def start_all_cameras(app, camera_urls):
    for i, cam_url in enumerate(camera_urls, start=1):
        cam_id = f"camera_{i}"
        capture_thread = threading.Thread(target=process_rtsp_stream_with_ffmpeg, args=(app, cam_id, cam_url), daemon=True)
        daemon=True #Ensures thread closes when main program exits
        capture_thread.start()

def init_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=lambda: scheduled_task(app), trigger='interval', hours=24)
    scheduler.start()
