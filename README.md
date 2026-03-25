🤖 AI Powered Fitness Tracker

This project is an AI-powered fitness tracker that uses computer vision to detect exercises in real-time. Built with Python, OpenCV, MediaPipe, and Streamlit, it provides an interactive web interface and tracks user performance metrics.

✨ Features
Real-time Exercise Detection: Detects squats using MediaPipe pose estimation
Repetition Counting: Automatically counts reps per session
User Progress Tracking: Stores stats in SQLite
Interactive Streamlit UI: Modern web interface
Chatbot Guidance: Provides tips, exercise instructions, and feedback
Visual Feedback: Highlights joints and calculates angles (hip, knee, ankle)
Login & Signup System: Personalized experience
Custom Styling: HTML/CSS templates for dashboard and pages

🎯 Technology Stack
Python 3.10 – Core programming
OpenCV – Video and image processing
MediaPipe – Pose estimation
Streamlit – Web app interface
SQLite – User data management
HTML/CSS – Templates and styling

🚀 Installation

Clone the repository:

git clone https://github.com/Mahin-Sabha/AI_Powered_Fitness_Tracker.git
cd AI_Powered_Fitness_Tracker

Create a virtual environment (optional but recommended):

python -m venv venv
# Activate
# Windows
venv\Scripts\activate
# Linux / Mac
source venv/bin/activate

Install dependencies:
pip install -r requirements.txt

🔧 Usage
streamlit run streamlit_app.py

Open the link in your browser (usually http://localhost:8501)
Signup or login to start tracking exercises
Use the chatbot for guidance during your workout
Perform squats in front of your webcam for real-time detection

🎮 Demo / GIFs

Replace these placeholders with your actual GIFs or screenshots

App Interface:
Chatbot Guidance:
Exercise Detection:

🏗️ Project Structure
AI_Powered_Fitness_Tracker/
├── app.py                # Core app logic
├── streamlit_app.py      # Streamlit interface
├── chatbot.py            # AI-guided chatbot
├── dashboard.py          # User progress dashboard
├── exercises.py          # Exercise detection and angle calculation
├── static/               # CSS styling
├── templates/            # HTML templates
├── users.db              # SQLite database
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation

📝 Usage Examples
Squat Detection: Stand in front of the webcam; app highlights joints and counts repetitions
Chatbot: Ask the bot questions like:
“How do I perform a proper squat?”
“Show my progress for today”
Dashboard: Visualize progress and exercise history

💡 Tips for Best Accuracy
Ensure good lighting
Keep entire body visible
Stand on a clear background for better pose estimation
Update requirements.txt if new packages are added

📄 License
This project is for learning and portfolio purposes only.
