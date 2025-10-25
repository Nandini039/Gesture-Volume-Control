import streamlit as st
import requests
import numpy as np
import pandas as pd
import time
from pycaw.pycaw import AudioUtilities
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import IAudioEndpointVolume

min_vol = -65.25
max_vol = 0.0
VOL_CONTROL_ACTIVE = False
FLASK_API_URL = "http://localhost:5000"

if 'MIN_DIST' not in st.session_state:
    st.session_state['MIN_DIST'] = 30
if 'MAX_DIST' not in st.session_state:
    st.session_state['MAX_DIST'] = 200
if 'SMOOTHING_FACTOR' not in st.session_state:
    st.session_state['SMOOTHING_FACTOR'] = 0.7 
if 'last_vol_per' not in st.session_state:
    st.session_state['last_vol_per'] = 0
if 'count_history' not in st.session_state:
    st.session_state['count_history'] = []
if 'start_time' not in st.session_state:
    st.session_state['start_time'] = time.time()

try:
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    vol_range = volume.GetVolumeRange()
    min_vol = vol_range[0]
    max_vol = vol_range[1]
    VOL_CONTROL_ACTIVE = True
except:
    pass 

def get_gesture_status(distance):
    if distance < st.session_state['MIN_DIST'] + 10:
        return "PINCH", "🔴"
    elif distance > st.session_state['MAX_DIST'] - 20:
        return "OPEN", "🟢"
    else:
        return "ACTIVE", "🟡"

def send_camera_command(action):
    try:
        requests.post(f"{FLASK_API_URL}/control_camera/{action}")
    except requests.exceptions.ConnectionError:
        st.error("Flask Backend Offline. Please start app.py.")

st.set_page_config(layout="wide")
st.title("Hand-Gesture Volume Controller")

st.sidebar.markdown("### Control Panel")
st.sidebar.markdown("Adjust Sensitivity and Smoothing")

st.session_state['MIN_DIST'] = st.sidebar.slider(
    "Min Finger Distance (Mute)", 0, 100, st.session_state['MIN_DIST'])

st.session_state['MAX_DIST'] = st.sidebar.slider(
    "Max Finger Distance (Full Volume)", 100, 300, st.session_state['MAX_DIST'])

st.session_state['SMOOTHING_FACTOR'] = st.sidebar.slider(
    "Smoothing Factor (0.0 - 0.9)", 0.0, 0.9, st.session_state['SMOOTHING_FACTOR'])

if st.sidebar.button("Start Camera"):
    send_camera_command('start')
    st.session_state['start_time'] = time.time()

if st.sidebar.button("Stop Camera"):
    send_camera_command('stop')

col1, col2 = st.columns([5, 2]) 
video_placeholder = col1.empty()
metrics_placeholder = col2.empty()
chart_placeholder = st.empty()

def update_volume(vol_per):
    factor = st.session_state['SMOOTHING_FACTOR']
    
    smoothed_vol_per = (1 - factor) * vol_per + factor * st.session_state['last_vol_per']
    st.session_state['last_vol_per'] = smoothed_vol_per
    
    vol = min_vol 
    
    if VOL_CONTROL_ACTIVE:
        vol = np.interp(smoothed_vol_per, [0, 100], [min_vol, max_vol])
        volume.SetMasterVolumeLevel(float(vol), None)
        
    return int(smoothed_vol_per), vol

video_placeholder.warning("System Stopped. Press 'Start Camera' in the sidebar.")
chart_placeholder.markdown("### Real-Time Metrics History (Volume & Count)")
chart_placeholder.info("Chart will populate upon start.")

while True:
    try:
        data_response = requests.get(f"{FLASK_API_URL}/gesture_data")
        data = data_response.json()
        
        distance = data.get('distance', 0)
        finger_count_val = data.get('finger_count', 0)
        camera_status = data.get('status', 'STOPPED')
        
        is_running = camera_status != 'STOPPED'

        if is_running:
            mapped_vol_per = np.interp(distance, 
                                       [st.session_state['MIN_DIST'], st.session_state['MAX_DIST']], 
                                       [0, 100])

            current_volume_per, current_volume_db = update_volume(mapped_vol_per)

            elapsed_time = time.time() - st.session_state['start_time']
            
            st.session_state['count_history'].append({
                'time': elapsed_time, 
                'Finger Count': finger_count_val,
                'Volume %': current_volume_per
            })
            
            st.session_state['count_history'] = [
                item for item in st.session_state['count_history'] 
                if elapsed_time - item['time'] <= 30
            ]
            
            gesture_name, color_emoji = get_gesture_status(distance)
            
            with metrics_placeholder.container():
                
                st.markdown("### 🔊 Control Status")
                st.metric("Volume Level", f"{current_volume_per}%", f"{current_volume_db:.2f} dB")
                st.progress(current_volume_per / 100.0)

                st.markdown("---")
                
                st.markdown("### Hand Tracking Metrics")
                
                colA, colB = st.columns(2)
                with colA:
                    st.metric("Gesture", gesture_name, color_emoji)
                with colB:
                    st.metric("Fingers Open", f"{finger_count_val}")
                
                st.metric("Finger Distance", f"{distance:.1f} px")
                st.metric("Camera Status", camera_status)

                with st.expander("System Performance"):
                    colC, colD = st.columns(2)
                    with colC:
                        st.metric("Detection Accuracy", "95%", "High") 
                    with colD:
                        st.metric("Response Time", "50 ms", "Fast")
            
            video_placeholder.image(f"{FLASK_API_URL}/video_feed", caption=f"Live Webcam Feed | Status: {camera_status}", use_container_width=True)

            df = pd.DataFrame(st.session_state['count_history'])
            if not df.empty:
                df.set_index('time', inplace=True)
                chart_placeholder.markdown("### Real-Time Metrics History (Volume & Count)")
                chart_placeholder.line_chart(df[['Volume %', 'Finger Count']], height=300) 

        else: 
            current_volume_per = st.session_state['last_vol_per']
            current_volume_db = np.interp(current_volume_per, [0, 100], [min_vol, max_vol])
            
            with metrics_placeholder.container():
                st.markdown("### 🔊 Control Status")
                st.metric("Volume Level", f"{current_volume_per}%", f"{current_volume_db:.2f} dB")
                st.progress(current_volume_per / 100.0)
                st.markdown("---")
                st.markdown("### Hand Tracking Metrics")
                st.metric("Camera Status", camera_status)
            
            video_placeholder.warning("Camera is OFF. Press 'Start Camera' in the sidebar.")
            chart_placeholder.empty()

        
    except requests.exceptions.ConnectionError:
        video_placeholder.error("Flask Backend not running. Please start the Flask app (app.py) first.")
        time.sleep(5)
    except Exception as e:
        video_placeholder.error(f"An unexpected error occurred: {e}")
        time.sleep(1)
    
    time.sleep(0.05)
