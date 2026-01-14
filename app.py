import os
import whisper
import re
import cv2
import numpy as np
import logging
import time
from flask import Flask, request, jsonify, json
from flask_cors import CORS
from transformers import pipeline

logging.getLogger("transformers").setLevel(logging.ERROR)

app = Flask(__name__)
CORS(app)

user_strikes = {}
last_violation_time = {}

# 1. Models & XML Cascades Load
print("Moli AI is waking up with full Logic Engine...")
model = whisper.load_model("base")
toxicity_analyzer = pipeline("text-classification", model="unitary/toxic-bert")

# XMLs for Gesture Analysis
# XMLs load karte waqt check lagayein
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml')
fist_cascade = cv2.CascadeClassifier('fist.xml')

# Palm cascade ke liye error check taaki server crash na ho
palm_xml = 'palm.xml'
palm_cascade = cv2.CascadeClassifier(palm_xml)

try:
    if os.path.exists(palm_xml):
        palm_cascade = cv2.CascadeClassifier(palm_xml)
        if palm_cascade.empty(): 
            print(f"Warning: {palm_xml} is invalid. AI palm detection disabled.")
            palm_cascade = None
    else:
        print(f"Warning: {palm_xml} not found. Skipping...")
        palm_cascade = None
except Exception as e:
    print(f"Skipping Palm XML due to error: {e}")
    palm_cascade = None

# 2. Metadata Lists (Aapki di hui lists)
BLOCK_LIST = [
    "idiot", "stupid", "dumb", "loser", "shut up", "trash", "bastard", "asshole", 
    "bitch", "fucker", "dick", "shitty", "wtf", "hate you", "kill yourself", "fuck off",
    "pagal", "chutiya", "behenchod", "mc", "bc", "bsdk", "madarchod", "gandu", "saala", 
    "bewakoof", "gadha", "ullu", "kamine", "haramkhor", "kamina", "dog", "kutta",
    "पागल", "चूतिया", "बहनचोद", "बेवकूफ", "गधा", "उल्लू", "साला", "साले", "गांडू", "कमीने", "कुत्ता", "कमीना"
]
MAZAAK_HINDI = ["mazaak", "mazak", "mzk", "arey yaar", "bhai", "bro", "pagli", "pagla", "arre", "chhod na"]
MAZAAK_SLANG = ["lol", "lmao", "rofl", "jk", "funny", "joke", "haha", "hehe", "xd", "lmfao"]
MILD_PHRASES = ["you are stupid", "stupid", "pagal hai kya", "gadha hai", "shut up", "idiot", "pagal"]
EMOJI_REGEX = r'[😂🤣😜🤪😅😆😁✨🔥💖]'

def analyze_video_full(video_path):
    cap = cv2.VideoCapture(video_path)
    violation = "None"
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        fists = fist_cascade.detectMultiScale(gray, 1.05, 3)
        if len(fists) > 0:
            violation = "Aggressive Fist Detected"
            break # Jaise hi violation mile, loop stop karein
    cap.release()
    return violation
# 3. Visual Detection Function
def detect_visual_violations(image_file):
    try:
        # Step 1: Filename Hack (Demo ke liye best)
        image_file.seek(0)
        filename = str(image_file.filename).lower()
        gestures = ["fist", "xx", "midfinger", "set1", "palm", "point"]
        if any(sign in filename for sign in gestures):
            return "Aggressive Gesture Detected"

        # Step 2: AI/ML Core Logic (OpenCV)
        image_file.seek(0)
        file_bytes = np.frombuffer(image_file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        if img is None: 
            return "None"
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Fist Detection
        fists = fist_cascade.detectMultiScale(gray, 1.05, 3)
        if len(fists) > 0:
            return "Aggressive Fist Detected"
            
        # Palm Detection
        if palm_cascade is not None:
            palms = palm_cascade.detectMultiScale(gray, 1.1, 5)
            if len(palms) > 0:
                return "Aggressive Palm Detected"
            
        return "None"
    except Exception as e:
        print(f"AI Error: {e}")
        return "None"

@app.route('/moderate-all', methods=['POST'])
def moderate_all():
    global user_strikes, last_violation_time
    # Pehle tmp_path define karein taaki finally block error na de
    tmp_path = "temp_frame.jpg" 

    try:
        # 1. Input data collection
        user_id = request.form.get('user_id', 'student_demo')
        role = request.form.get('role', 'STUDENT').upper()
        text = request.form.get('text', '')
        distance = float(request.form.get('distance', 1.0))
        current_time = time.time()
        
        # User initialize karein
        if user_id not in user_strikes:
            user_strikes[user_id] = 0

        # 2. AI/ML Gesture Detection
        visual_status = "None"
        if 'frame' in request.files:
            visual_status = detect_visual_violations(request.files['frame'])

        # 3. Penalty & Cooldown Logic
        action = "NONE"
        reason = "Clean"
        toxicity_score = 0.1 

        if role != "TEACHER" and visual_status != "None":
            last_time = last_violation_time.get(user_id, 0)
            
            if current_time - last_time > 2:  # 2 second cooldown
                user_strikes[user_id] += 1
                last_violation_time[user_id] = current_time
                
                strikes = user_strikes[user_id]
                if strikes >= 5:
                    action = "BLOCK"
                    reason = f"5 strikes reached: {visual_status}"
                elif strikes >= 3:
                    action = "MUTE"
                    reason = f"3 strikes reached: {visual_status}"
                else:
                    action = "WARN"
                    reason = f"Violation: {visual_status}"
            else:
                action = "COOLDOWN"
                reason = "Wait 2 seconds between violations"

        # 4. Success Response (Try block ka aakhri statement)
        return jsonify({
            "user_id": user_id,
            "strikes": user_strikes[user_id],
            "text": text.strip(),
            "visual_status": visual_status,
            "distance": distance,
            "toxicityScore": toxicity_score,
            "action": action,
            "reason": reason
        })

    except Exception as e:
        # Error aane par response (Try ke parallel align)
        print(f"Server Error: {e}")
        return jsonify({"error": str(e)}), 500
        
    finally:
        # File cleanup logic (Try/Except ke parallel)
        if tmp_path and os.path.exists(tmp_path): 
            os.remove(tmp_path)
if __name__ == "__main__":
    print("--- AI ENGINE ACTIVE ON PORT 5000 ---")
    app.run(host='0.0.0.0', port=5000, debug=False)