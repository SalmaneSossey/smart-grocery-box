#!/usr/bin/env python3
"""Simple camera test script to verify camera functionality."""

import cv2
import sys

def test_camera(camera_id=0):
    """Test if the camera is working and display the feed."""
    print(f"Testing camera {camera_id}...")
    
    # Try to open the camera
    cap = cv2.VideoCapture(camera_id)
    
    if not cap.isOpened():
        print(f"❌ ERROR: Cannot open camera {camera_id}")
        return False
    
    # Read camera properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"✓ Camera {camera_id} opened successfully")
    print(f"  Resolution: {width}x{height}")
    print(f"  FPS: {fps}")
    
    # Try to read a frame
    ret, frame = cap.read()
    
    if not ret:
        print(f"ERROR: Cannot read frame from camera {camera_id}")
        cap.release()
        return False
    
    print(f"✓ Successfully captured frame")
    print(f"  Frame shape: {frame.shape}")
    
    print("\nPress 'q' to quit the camera preview")
    print("Camera feed is displaying...")
    
    # Display video feed
    frame_count = 0
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print(f"ERROR: Lost camera connection")
            break
        
        frame_count += 1
        
        # Add frame counter to display
        cv2.putText(frame, f"Frame: {frame_count}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Press 'q' to quit", (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow(f'Camera {camera_id} Test', frame)
        
        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print(f"\n✓ Camera test completed. Captured {frame_count} frames.")
            break
    
    cap.release()
    cv2.destroyAllWindows()
    return True


def scan_cameras(max_ports=5):
    """Scan for available cameras."""
    print(f"Scanning for cameras (ports 0-{max_ports-1})...\n")
    available = []
    
    for port in range(max_ports):
        cap = cv2.VideoCapture(port)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                available.append(port)
                print(f"✓ Camera found on port {port}")
            cap.release()
        else:
            print(f"  Port {port}: No camera")
    
    return available


if __name__ == "__main__":
    print("=" * 50)
    print("Camera Test Tool")
    print("=" * 50 + "\n")
    
    # First, scan for available cameras
    available_cameras = scan_cameras()
    
    if not available_cameras:
        print("\n No cameras found!")
        print("\nTroubleshooting tips:")
        print("  1. Check if camera is connected")
        print("  2. Try: ls -l /dev/video*")
        print("  3. Try: v4l2-ctl --list-devices")
        print("  4. Check permissions: groups $USER")
        sys.exit(1)
    
    print(f"\nFound {len(available_cameras)} camera(s): {available_cameras}")
    
    # Determine which camera to test
    if len(sys.argv) > 1:
        camera_id = int(sys.argv[1])
    else:
        camera_id = available_cameras[0]
    
    print(f"\nTesting camera {camera_id}...\n")
    
    # Test the camera
    success = test_camera(camera_id)
    
    if success:
        print("\n✓ Camera is working properly!")
    else:
        print("\n Camera test failed!")
        sys.exit(1)
