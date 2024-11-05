import ffmpeg
import numpy as np

def capture_frame_from_url(url, width=1280, height=720):
    """Uses ffmpeg to capture a frame from a video stream URL."""
    process = (
        ffmpeg
        .input(url)
        .output('pipe:', format='rawvideo', pix_fmt='bgr24', vframes=1)
        .run_async(pipe_stdout=True)
    )

    # Read frame bytes from stdout
    in_bytes = process.stdout.read(width * height * 3)
    process.stdout.close()
    process.wait()

    if in_bytes:
        return np.frombuffer(in_bytes, np.uint8).reshape([height, width, 3])
    return None