import cv2
import mediapipe as mp
import math
import numpy as np
from flask import Flask, Response, jsonify, request
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import threading
import time

app = Flask(__name__)

global_data = {
    'frame': None,
    'distance': 0,
    'vol_per': 0,
    'finger_count': 0,
    'status': 'STOPPED',
}

CAMERA_ACTIVE = threading.Event()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)
mp_draw = mp.solutions.drawing_utils
cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
vol_range = volume.GetVolumeRange()
min_vol = vol_range[0]
max_vol = vol_range[1]


MIN_DIST = 30
MAX_DIST = 200
tip_ids = [4, 8, 12, 16, 20]

def finger_count(landmarks):
    fingers_up = []
    
    if landmarks.landmark[tip_ids[0]].x < landmarks.landmark[tip_ids[0] - 1].x:
        fingers_up.append(1)
    else:
        fingers_up.append(0)
        
    for id in range(1, 5):
        if landmarks.landmark[tip_ids[id]].y < landmarks.landmark[tip_ids[id] - 2].y:
            fingers_up.append(1)
        else:
            fingers_up.append(0)

    return sum(fingers_up)

def process_frame():
    global global_data
    
    while cap.isOpened():
        CAMERA_ACTIVE.wait() 
        
        success, img = cap.read()
        if not success:
            continue
        
        img = cv2.flip(img, 1)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)
        
        distance = 0
        finger_count_val = 0
        vol_per = 0
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                h, w, c = img.shape
                x1, y1 = int(hand_landmarks.landmark[4].x * w), int(hand_landmarks.landmark[4].y * h)
                x2, y2 = int(hand_landmarks.landmark[8].x * w), int(hand_landmarks.landmark[8].y * h)
                
                distance = math.hypot(x2 - x1, y2 - y1)
                
                cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
                cv2.circle(img, (x1, y1), 10, (255, 0, 255), cv2.FILLED)
                cv2.circle(img, (x2, y2), 10, (255, 0, 255), cv2.FILLED)
                
                vol_per = np.interp(distance, [MIN_DIST, MAX_DIST], [0, 100])
                finger_count_val = finger_count(hand_landmarks)
                
                cv2.putText(img, f'Fingers: {finger_count_val}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

            global_data['status'] = 'ACTIVE'
        else:
            global_data['status'] = 'IDLE'

        cv2.putText(img, f'Distance: {distance:.1f}px', (10, 30), cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 255, 255), 2)
        
        ret, buffer = cv2.imencode('.jpg', img)
        frame_bytes = buffer.tobytes()
        
        global_data['distance'] = float(distance)
        global_data['vol_per'] = float(vol_per)
        global_data['finger_count'] = finger_count_val
        global_data['frame'] = frame_bytes
        
        time.sleep(0.033)

def generate_frames():
    while True:
        if CAMERA_ACTIVE.is_set() and global_data['frame']:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + global_data['frame'] + b'\r\n')
        elif not CAMERA_ACTIVE.is_set():
            time.sleep(0.5)
        else:
            time.sleep(0.1)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/gesture_data')
def gesture_data():
    return jsonify({
        'distance': global_data['distance'],
        'vol_per': global_data['vol_per'],
        'finger_count': global_data['finger_count'],
        'status': global_data['status'],
    })

@app.route('/control_camera/<action>', methods=['POST'])
def control_camera(action):
    if action == 'start':
        CAMERA_ACTIVE.set()
        global_data['status'] = 'STARTING'
        return jsonify({'status': 'Camera started successfully'}), 200
    elif action == 'stop':
        CAMERA_ACTIVE.clear()
        global_data['status'] = 'STOPPED'
        return jsonify({'status': 'Camera stopped successfully'}), 200
    return jsonify({'error': 'Invalid action'}), 400

threading.Thread(target=process_frame, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)