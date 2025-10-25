🔊 Volume Control Using Hand Gesture 

Project Overview
This application is a real-time Human-Computer Interaction (HCI) system that enables touchless control over your computer's master audio volume using a webcam. The core function is to track a simple hand gesture and precisely map the measured distance to the system's sound level.

How It Works

Vision Processor (app.py): The system uses MediaPipe to detect the 21 landmarks of your hand. It focuses on the distance between the Thumb Tip and the Index Finger Tip.

Control Logic: The pixel distance is calculated, and NumPy maps that value to the specific decibel range required by your operating system.

System Output: PyCaw (on Windows) then applies the precise volume change, and Streamlit renders the visual dashboard, including the live video feed and a dynamic volume bar.

🛠️ Project Components

The project runs on a decoupled architecture using two main files:

app.py (Backend): This is the Processing Engine. It handles the webcam input, runs the MediaPipe hand tracking, calculates the finger distance and count, and serves all data via an API.

streamlit_app.py (Frontend): This is the User Interface and Control Layer. It fetches the real-time data from Flask, executes the PyCaw volume change, and displays the interactive dashboard and charts.

🚀 Getting Started

Prerequisites

You need Python 3.8+, a functional Webcam, and a Windows OS (required for the PyCaw volume control library).

Installation and Setup

Activate Virtual Environment (Recommended):
Bash

.\venv\Scripts\activate

Install Dependencies:

Bash

pip install -r requirements.txt

▶️ How to Run the System
The system requires two separate terminals to run the backend and frontend simultaneously.

Terminal 1: Start the Vision Processor (Backend)
Bash

python app.py

Terminal 2: Start the Dashboard (Frontend)
Bash

streamlit run streamlit_app.py

Control Usage

The dashboard will open in your browser.

To lower the volume, pinch your thumb and index finger closer together.

To raise the volume, spread your fingers apart.
