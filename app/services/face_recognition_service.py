from app.repositories.employee_repository import EmployeeRepository
from datetime import datetime, timedelta
import face_recognition
import cv2
import psutil
import gc
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch

class FaceRecognitionService:
    last_face_locations = {}
    # Track face positions and action timestamps to avoid rapid re-logging
    last_face_positions = {}  # Stores previous y-coordinates of faces by employee ID
    last_logged_action = {}  # Stores last logged actions by employee ID with timestamps

    ENTRY_EXIT_THRESHOLD = 50  # Pixels threshold to determine movement direction
    LOGGING_COOLDOWN = timedelta(seconds=3)  # Cooldown period to avoid excessive logging

    mtcnn = MTCNN(keep_all=True, device='cuda' if torch.cuda.is_available() else 'cpu')
    resnet = InceptionResnetV1(pretrained='vggface2').eval().to('cuda' if torch.cuda.is_available() else 'cpu')

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
                # rgb_frame = frame[:, :, ::-1]
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
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
                faces, probs = FaceRecognitionService.mtcnn.detect(rgb_frame)
                if faces is None:
                    print("No faces detected in the frame.")
                    return
                faces = [face for face, prob in zip(faces, probs) if prob > 0.9]  
                print('Faces detected') # Filter based on detection confidence

                aligned_faces = []
                for face in faces:
                    x1, y1, x2, y2 = map(int, face)
                    aligned_face = rgb_frame[y1:y2, x1:x2]
                    aligned_face = cv2.resize(aligned_face, (160, 160))  # Resize for the model
                    aligned_face = torch.tensor(aligned_face).permute(2, 0, 1).unsqueeze(0).float() / 255.0
                    if torch.cuda.is_available():
                        aligned_face = aligned_face.to('cuda')
                    aligned_faces.append(aligned_face)
                    # aligned_faces.append(FaceRecognitionService.mtcnn.extract(aligned_face))

                embeddings = [FaceRecognitionService.resnet(face).detach().cpu().numpy() for face in aligned_faces]
                # embeddings = [FaceRecognitionService.resnet(face.unsqueeze(0)) for face in aligned_faces]
                # face_locations = face_recognition.face_locations(rgb_frame)
                # if len(face_locations) == 0:
                #     print(f"No faces detected in the frame.")
                #     return        
                # print('located faces')
                # face_encodings = face_recognition.face_encodings(frame, face_locations)
                # print('encodings done')

                for i, embedding in enumerate(embeddings):
                    print('making repo service call')
                    employee = EmployeeRepository.find_by_face_data(embedding)
                    print('fetched employee by face data from DB')
                    face_location = faces[i]
                    action = FaceRecognitionService.get_movement_action(face_location, cam_id, employee)
                    print(f'detected the action {action}')
                    if action == None:
                        action = 'No_movement'
                    if employee:
                        EmployeeRepository.add_entry_exit(employee.id, employee.employee_name, cam_id, action)
                    elif action is not None:
                        EmployeeRepository.add_entry_exit(0, 'Unknown', cam_id, action)
            except Exception as e:
                print(f"[Error] Failed to process frame for camera ID {cam_id}: {e}")
            finally:
                gc.collect()
                print(f"garbage collecting..")

    @staticmethod
    def get_movement_action(face_location, cam_id, employee):
        employee_id = employee.id if employee else "unknown"
        top, right, bottom, left = map(int, face_location)
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

    @staticmethod
    def encode_face(image_file):
        """Convert an uploaded image file into a face encoding."""
        image = cv2.imread(image_file)  # Read the image from file
        if image is None:
            print("[Error] Failed to read image file.")
            return None
        
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        faces, probs = FaceRecognitionService.mtcnn.detect(rgb_image)
        
        if faces is None or len(faces) == 0:
            print("[Error] No faces detected in the image.")
            return None

        # Filter faces based on a confidence threshold (0.9 in this example)
        high_conf_faces = [face for face, prob in zip(faces, probs) if prob > 0.9]
        
        if not high_conf_faces:
            print("[Error] No faces met the confidence threshold.")
            return None
        
        # Using the first detected face
        x1, y1, x2, y2 = map(int, high_conf_faces[0])
        aligned_face = rgb_image[y1:y2, x1:x2]
        aligned_face = cv2.resize(aligned_face, (160, 160))  # Resize to model input size

        # Convert to tensor and normalize for the model
        aligned_face_tensor = torch.tensor(aligned_face).permute(2, 0, 1).unsqueeze(0).float() / 255.0
        if torch.cuda.is_available():
            aligned_face_tensor = aligned_face_tensor.to('cuda')

        # Generate embedding using the model
        face_encoding = FaceRecognitionService.resnet(aligned_face_tensor).detach().cpu().numpy()
        
        return face_encoding