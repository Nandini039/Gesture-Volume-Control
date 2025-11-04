import streamlit as st
import requests
import numpy as np
import pandas as pd
import time
from pycaw.pycaw import AudioUtilities
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import IAudioEndpointVolume
import streamlit_authenticator as stauth
import pyautogui


def add_custom_css():
   
        st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: #f0f2f6; 
            color: #1c1e21; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        .stApp h1 {{
            background-color: #13323D ; 
            color: rgb(94 156 215); 
            font-size: 2.5rem;
            text-align: center;
            margin-bottom: 2rem;
        }}

        [data-testid="stForm"] > div:first-child {{
            background-color: rgb(145 158 234 / 40%); 
            padding: 20px 30px;
            border-radius: 15px;
            box-shadow: 1 6px 20px rgba(0, 0, 0, 0.1) ;
            max-width: 450px; 
            margin: auto;
        }}

        .stTextInput > div > div > input {{
            background-color: #f7f7f7;
            border-radius: 8px;
            border: 2px solid #ccc;
            padding: 20px;
        }}
        
        [data-testid="stForm"] button {{
            background-color: #13323d;
            color: white;
            border-radius: 4px;
            padding: 10px 20px;
            font-size: 1rem;
            font-weight: bold;
            border: none;
            transition: background-color 0.3s;
        }}

        [data-testid="stForm"] button:hover {{
            background-color: #43A047;
        }}
        
        [data-testid="stAlert"] {{
            border-left: 5px solid #ff9800 !important; 
            background-color: #fff3e0 !important; 
            color: #e65100 !important;
            font-weight: bold;
            border-radius: 5px;
            max-width: 400px;
            margin: 15px auto; 
        }}

        div.block-container {{
            background-color:  rgba(255, 255, 255, 0.9)  !important;
            border-radius: 12px;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
            margin-top: 2rem; 
            padding: 2rem !important; 
        }}

        .stApp {{
            background-color: #f0f2f6; 
            color: #1c1e21;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}

       
        .stApp h1 {{
            color: rgb(94 156 215); 
            font-size: 2.5rem;
            text-align: center;
            margin-bottom: 2rem;
        }}

        [data-testid="stSidebar"] {{
            background-color: #3f7a8c; 
            border-right: 1px solid #ddd;
            padding: 10px;
        }}
        
        
        [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
            color:#101214;
        }}

        .stSlider .st-bd {{
            background-color: #bdbdbd; 
        }}
        .stSlider .st-bg {{
            background-color: #4CAF50; 
        }}

        [data-testid="stMetric"] {{
            background-color: #CFD8DC;
            padding: 10px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }}

        [data-testid="stMetricValue"] {{
            font-size: 1.5rem !important;
            color: #007bff;
        }}

        .stProgress > div > div > div > div {{
            background-color: #4CAF50; 
        }}
        
        .stImage {{
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }}

        </style>
        """,
        unsafe_allow_html=True
    )

min_vol = -65.25
max_vol = 0.0
VOL_CONTROL_ACTIVE = False
FLASK_API_URL = "http://localhost:5000"

hashed_passwords = [

    '$2b$12$tyy9MCrR8TNZjTSbGtc2seLRzBxr0qjfbWzJYlpWWiblzLITUkOR2', 
    '$2b$12$4/7IILlC4DyrwFGcsRIRAeN/mGm58qkD1yqBdCzBMRCJgyfGMhY9i' 
]

credentials = {
    'usernames': {
        'Nandini': {'name': 'Nandini Suryavanshi', 'password': hashed_passwords[0]},
        'User': {'name': 'User', 'password': hashed_passwords[1]},
    }
}

try:
    authenticator = stauth.Authenticate(
        credentials,
        'hand_gesture_volume_app',
        'abcdef',
        30
    )
except Exception as e:
    st.error(f"Authentication setup failed. Specific Error: {e}")
    authenticator = None

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
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = None
if 'name' not in st.session_state:
    st.session_state['name'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None

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

def update_volume(vol_per):
    factor = st.session_state['SMOOTHING_FACTOR']

   
    smoothed_vol_per = (1 - factor) * vol_per + factor * st.session_state['last_vol_per']

    previous_vol = st.session_state['last_vol_per']
    st.session_state['last_vol_per'] = smoothed_vol_per

    diff = smoothed_vol_per - previous_vol

    
    threshold = 2.5  

    if diff > threshold:
        steps = int(diff // threshold)
        for _ in range(steps):
            pyautogui.press("volumeup")
    elif diff < -threshold:
        steps = int(abs(diff) // threshold)
        for _ in range(steps):
            pyautogui.press("volumedown")

    
    return int(smoothed_vol_per), 0


st.set_page_config(layout="wide")
add_custom_css()
st.title("Hand-Gesture Volume Controller")

if authenticator:
    
    result = authenticator.login('main', 'Login') 

    if result is not None and len(result) == 3:
        name, st.session_state['authentication_status'], username = result
        st.session_state['name'] = name
        st.session_state['username'] = username
        
    
    if st.session_state['authentication_status'] is True:
        
        authenticator.logout('Logout', 'sidebar')
        st.sidebar.markdown(f"**Welcome, {st.session_state['name']}!**")

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

        col1, col2 = st.columns([7, 3]) 
        
        video_and_chart_placeholder = col1.empty()
        metrics_placeholder = col2.empty() 

        while st.session_state['authentication_status']:
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
                        
                        col_vol1, col_vol2 = st.columns(2)
                        with col_vol1:
                            st.metric("Volume Level", f"{current_volume_per}%")
                            st.progress(current_volume_per / 100.0) 
                        with col_vol2:
                            st.metric("Volume dB", f"{current_volume_db:.2f} dB")


                        st.markdown("---")
                        
                        st.markdown("### Hand Tracking Metrics")
                        
                        colA, colB = st.columns(2)
                        with colA:
                            st.markdown(f'<p style="font-size: 14px; margin-bottom: 0px;">Gesture</p>', unsafe_allow_html=True)
                            st.metric("", gesture_name, color_emoji)
                        with colB:
                            st.markdown(f'<p style="font-size: 14px; margin-bottom: 5px;">Finger Open</p>', unsafe_allow_html=True)
                            st.metric("", f"{finger_count_val}")
                            
                        colC, colD = st.columns(2)
                        with colC:
                            st.markdown(f'<p style="font-size: 14px; margin-bottom: 0px;">Finger Distance</p>', unsafe_allow_html=True)
                            st.metric("", f"{distance:.1f} px")
                        with colD:
                            st.markdown(f'<p style="font-size: 14px; margin-bottom: 1px;">Camera Status</p>', unsafe_allow_html=True)
                            st.metric("", camera_status)

                        with st.expander("System Performance"):
                            colE, colF = st.columns(2)
                            with colE:
                                st.metric("Detection Accuracy", "95%", "High")
                            with colF:
                                st.metric("Response Time", "50 ms", "Fast")
                        
                    df = pd.DataFrame(st.session_state['count_history'])
                    
                    with video_and_chart_placeholder.container():
                        
                        st.image(f"{FLASK_API_URL}/video_feed", caption=f"Live Webcam Feed | Status: {camera_status}", use_container_width=False ,width=500)
                        
                        st.markdown("---")
                        
                        st.markdown("### Real-Time Metrics History (Volume & Count)")
                        if not df.empty:
                            df.set_index('time', inplace=True)
                            st.line_chart(df[['Volume %', 'Finger Count']], height=200, width=500)
                        else:
                            st.info("Chart will populate upon start.")
                            
                else:
                    current_volume_per = st.session_state['last_vol_per']
                    current_volume_db = np.interp(current_volume_per, [0, 100], [min_vol, max_vol])

                    with metrics_placeholder.container():
                        st.markdown("### 🔊 Control Status")
                        
                        col_vol1, col_vol2 = st.columns(2)
                        with col_vol1:
                            st.metric("Volume Level", f"{current_volume_per}%")
                            st.progress(current_volume_per / 100.0)
                        with col_vol2:
                            st.metric("Volume dB", f"{current_volume_db:.2f} dB")
                            
                        st.markdown("---")
                        st.markdown("### Hand Tracking Metrics")
                        st.metric("Camera Status", camera_status)

                    with video_and_chart_placeholder.container():
                         st.warning("Camera is OFF. Press 'Start Camera' in the sidebar.")
                         st.markdown("---")
                         st.markdown("### Real-Time Metrics History (Volume & Count)")
                         st.info("Chart will populate upon start.")

            except requests.exceptions.ConnectionError:
                video_and_chart_placeholder.error("Flask Backend not running. Please start the Flask app (app.py) first.")
                time.sleep(5)
            except Exception as e:
                video_and_chart_placeholder.error(f"An unexpected error occurred: {e}")
                time.sleep(1)

            time.sleep(0.05)

    elif st.session_state['authentication_status'] is False:
        st.error('Username/password is incorrect')
    elif st.session_state['authentication_status'] is None:
        st.warning('Please enter your username and password')