import cv2
import time
from utils.helpers import setup_logger

logger = setup_logger("FaceSec")

class FaceAuthenticator:
    def __init__(self):
        # We use a standard pre-trained Haar Cascade for frontal face detection
        self.cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(self.cascade_path)

    def verify_user(self) -> bool:
        """
        Briefly turns on the webcam, checks for a face to authenticate.
        If a face is detected within 3 seconds, returns True.
        """
        logger.info("Initializing Biometric Authentication...")
        
        try:
            # 0 usually points to the default built-in webcam
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                logger.error("Webcam not found or accessible.")
                return False

            start_time = time.time()
            face_detected = False

            # Check for 3 seconds maximum
            while (time.time() - start_time) < 3.0:
                ret, frame = cap.read()
                if not ret:
                    continue

                # Convert to grayscale for cascade detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Detect faces
                faces = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )

                if len(faces) > 0:
                    logger.info("Face securely identified. Access granted.")
                    face_detected = True
                    break
                time.sleep(0.1)

            cap.release()
            
            if not face_detected:
                logger.warning("No face match detected. Access denied.")
            
            return face_detected

        except Exception as e:
            logger.error(f"Biometric system error: {e}")
            return False
