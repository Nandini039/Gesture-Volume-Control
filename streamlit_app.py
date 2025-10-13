import streamlit as st
import requests
import numpy as np
import pandas as pd
import time
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL

try:
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    vol_range = volume.GetVolumeRange()
    min_vol = vol_range[0]
    max_vol = vol_range[1]
    VOL_CONTROL_ACTIVE = True
except:
    VOL_CONTROL_ACTIVE = False

st.set_page_config(layout="wide")
st.title("Gesture-Based Volume Control & Finger Counter")

col1, col2 = st.columns([2, 1])
video_placeholder = col1.empty()
stats_placeholder = col2.empty()

if 'last_vol_per' not in st.session_state:
    st.session_state.last_vol_per = 0
if 'count_history' not in st.session_state:
    st.session_state.count_history = []
if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()

st.header("Finger Counts Over Time")
chart_placeholder = st.empty()

FLASK_API_URL = "http://localhost:5000"

def update_volume(vol_per):
    smoothed_vol_per = 0.8 * vol_per + 0.2 * st.session_state.last_vol_per
    st.session_state.last_vol_per = smoothed_vol_per
    
    if VOL_CONTROL_ACTIVE:
        vol = np.interp(smoothed_vol_per, [0, 100], [min_vol, max_vol])
        volume.SetMasterVolumeLevel(float(vol), None)
        
    return int(smoothed_vol_per)

while True:
    try:
        data_response = requests.get(f"{FLASK_API_URL}/gesture_data")
        data = data_response.json()
        
        distance = data.get('distance', 0)
        vol_per = data.get('vol_per', 0)
        finger_count_val = data.get('finger_count', 0)

        current_volume_per = update_volume(vol_per)

        elapsed_time = time.time() - st.session_state.start_time
        st.session_state.count_history.append({'time': elapsed_time, 'Finger Count': finger_count_val})
        
        st.session_state.count_history = [
            item for item in st.session_state.count_history 
            if elapsed_time - item['time'] <= 30
        ]
        
        df = pd.DataFrame(st.session_state.count_history)
        if not df.empty:
            df.set_index('time', inplace=True)
            chart_placeholder.line_chart(df)
            
        with stats_placeholder.container():
            st.header("Current Volume")
            st.markdown(f"## {current_volume_per}%")
            st.progress(current_volume_per / 100.0)
            
            st.header("Gesture Metrics")
            st.info(f"**Distance**: {distance:.1f} px")
            st.warning(f"**Fingers Up**: **{finger_count_val}**")

        video_placeholder.image(f"{FLASK_API_URL}/video_feed", caption="Live Gesture Control", use_container_width=True)

        
    except requests.exceptions.ConnectionError:
        video_placeholder.error("Flask Backend not running. Please start the Flask app (app.py) first.")
        time.sleep(5)
    except Exception as e:
        video_placeholder.error(f"An unexpected error occurred: {e}")
        time.sleep(1)
    
    time.sleep(0.05)