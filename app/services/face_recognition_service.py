from app.repositories.employee_repository import EmployeeRepository
from datetime import datetime, timedelta
import face_recognition
import cv2
import psutil
import gc

class FaceRecognitionService:
    last_face_locations = {}
    # Track face positions and action timestamps to avoid rapid re-logging
    last_face_positions = {}  # Stores previous y-coordinates of faces by employee ID
    last_logged_action = {}  # Stores last logged actions by employee ID with timestamps

    ENTRY_EXIT_THRESHOLD = 50  # Pixels threshold to determine movement direction
    LOGGING_COOLDOWN = timedelta(seconds=3)  # Cooldown period to avoid excessive logging

    @staticmethod
    def process_camera_feed(frame, cam_id):
        while True:
            print(f'In processing camera feed in cam ID: {cam_id}')
            # Monitor and log resource usage
            memory_usage = psutil.virtual_memory().percent
            cpu_usage = psutil.cpu_percent(interval=1)
            print(f"[Resource Monitor] Memory Usage: {memory_usage}%, CPU Usage: {cpu_usage}%")
            if frame is None or frame.size == 0:
                print(f"[Error] Empty frame for camera ID {cam_id}. Skipping processing.")
                return  # Skip processing if the frame is empty
            print(f"[DEBUG] Frame received: {frame is not None}, frame size: {frame.size if frame is not None else 'None'}")
            try:
                rgb_frame = frame[:, :, ::-1]
                print('rgb framed')
                # Check the size of the RGB frame to ensure it's not too small
                if rgb_frame.shape[0] < 50 or rgb_frame.shape[1] < 50:
                    print(f"[Error] Frame size too small: {rgb_frame.shape}. Skipping frame.")
                    return
                    # rgb_frame = cv2.resize(rgb_frame, (640, 480))
                    # print(f'Frame Resized to {rgb_frame}')
                print('rgb frame size accepted')
                if rgb_frame.shape[0] > 720 or rgb_frame.shape[1] > 480:
                    if psutil.virtual_memory().percent < 75:
                        print("Processing at high resolution for accuracy.")
                    else:
                        print("Downscaling to manage resource usage.")
                        rgb_frame = cv2.resize(rgb_frame, (640, 480))
                        print('Resize done')
                face_locations = face_recognition.face_locations(rgb_frame)
                if len(face_locations) == 0:
                    print(f"No faces detected in the frame.")
                    return        
                print('located faces')
                face_encodings = face_recognition.face_encodings(frame, face_locations)
                print('encodings done')

                for i, face_encoding in enumerate(face_encodings):
                    print('making repo service call')
                    employee = EmployeeRepository.find_by_face_data(face_encoding)
                    print('fetched employee by face data from DB')
                    face_location = face_locations[i]
                    action = FaceRecognitionService.get_movement_action(face_location, cam_id, employee)
                    print(f'detected the action {action}')
                    if action == None:
                        action = 'No_movement'
                    if employee:
                        EmployeeRepository.add_entry_exit(employee.id, employee.empoyee_name, cam_id, action)
                    elif action is not None:
                        EmployeeRepository.add_entry_exit(0, 'Unknown', cam_id, 'entry')
            except Exception as e:
                print(f"[Error] Failed to process frame for camera ID {cam_id}: {e}")
            finally:
                gc.collect()
                print(f"garbage collecting..")

    @staticmethod
    def get_movement_action(face_location, cam_id, employee):
        employee_id = employee.id if employee else "unknown"
        top, right, bottom, left = face_location
        face_center_y = (top + bottom) // 2  # Using center y-coordinate as a proxy for distance

        # Retrieve the last known position and timestamp for the employee
        last_position = FaceRecognitionService.last_face_positions.get(employee_id, {}).get(cam_id)
        last_action_time = FaceRecognitionService.last_logged_action.get(employee_id, {}).get(cam_id)
        # Determine if action should be logged based on movement direction
        if last_position is not None:
            # Calculate the movement direction
            if face_center_y < last_position - FaceRecognitionService.ENTRY_EXIT_THRESHOLD:
                action = "entry"  # Moving closer to the camera
            elif face_center_y > last_position + FaceRecognitionService.ENTRY_EXIT_THRESHOLD:
                action = "exit"  # Moving away from the camera
            else:
                return None  # No significant movement, so no action is logged

            # Check if the action was recently logged to prevent duplicate entries
            if last_action_time and datetime.utcnow() - last_action_time < FaceRecognitionService.LOGGING_COOLDOWN:
                return None  # Skip logging this action if cooldown is active

            # Update the last action time and position
            FaceRecognitionService.last_logged_action.setdefault(employee_id, {})[cam_id] = datetime.utcnow()
            FaceRecognitionService.last_face_positions.setdefault(employee_id, {})[cam_id] = face_center_y

            return action

        #First detection - initialize position tracking but don’t log an action yet
        FaceRecognitionService.last_face_positions.setdefault(employee_id, {})[cam_id] = face_center_y
        return None

    # use below function incase of adding new employee image in DB by capturing from local cam on hitting addEmployee endpoint
    # @staticmethod
    # def capture_employee_image():
    #     video_capture = cv2.VideoCapture(0)
    #     ret, frame = video_capture.read()
    #     video_capture.release()

    #     if not ret:
    #         print("Failed to capture image")
    #         return None
        
    #     # Convert the captured frame to face encoding
    #     rgb_frame = frame[:, :, ::-1]  # Convert BGR to RGB
    #     face_encodings = face_recognition.face_encodings(rgb_frame)
    #     if not face_encodings:
    #         return jsonify({"error": "No face detected in captured image"}), 400
    #     print('Face is detected and captured')
    #     face_encoding = face_encodings[0]
    #     print('Returning First element in face encodings')
    #     #new_employee = EmployeeService.add_employee(name, face_encoding)
    #     # Convert the frame to bytes for storage
    #     #_, buffer = cv2.imencode('.jpg', frame)
    #     #image_data = buffer.tobytes()
    #     return face_encoding

    @staticmethod
    def encode_face(image_file):
        """Convert an uploaded image file into a face encoding."""
        image = face_recognition.load_image_file(image_file)
        face_encodings = face_recognition.face_encodings(image)
        if face_encodings:
            return face_encodings[0]  # Use the first face found
        return None

