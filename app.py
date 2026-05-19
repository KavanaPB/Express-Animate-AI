from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import requests
import time
import os
import json
from datetime import datetime
import base64

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "static/uploads"
app.config['VIDEO_FOLDER'] = "static/videos"
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['VIDEO_FOLDER'], exist_ok=True)

# API Keys
MISTRAL_API_KEY = "API key "
ELEVENLABS_KEY = "API key"
STABILITY_KEY = "API key"
LUMA_API_KEY = "luma-API key"

# Luma API Configuration
LUMA_BASE_URL = "https://api.lumalabs.ai/dream-machine/v1"

# Initialize Mistral AI client
mistral_client = OpenAI(
    api_key=MISTRAL_API_KEY,
    base_url="https://api.mistral.ai/v1"
)

# ================= IMAGE =================
def generate_stability_image(prompt):
    try:
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        
        headers = {
            "Authorization": f"Bearer {STABILITY_KEY}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        payload = {
            "text_prompts": [{"text": f"cinematic scene, {prompt}", "weight": 1}],
            "height": 1024,
            "width": 1024,
            "samples": 1,
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            result = response.json()
            img_base64 = result["artifacts"][0]["base64"]

            filename = f"image_{int(time.time())}.png"
            path = os.path.join("static", filename)

            with open(path, "wb") as f:
                f.write(base64.b64decode(img_base64))

            return f"/static/{filename}"

    except:
        return None


# ================= AUDIO =================
def generate_audio(script):
    url = "https://api.elevenlabs.io/v1/text-to-speech/nPczCjzI2devNBz1zQrb"

    headers = {
        "xi-api-key": ELEVENLABS_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }

    payload = {"text": script[:500]}

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        return None

    os.makedirs("static/audio", exist_ok=True)
    filename = f"audio_{int(time.time())}.mp3"
    path = os.path.join("static/audio", filename)

    with open(path, "wb") as f:
        f.write(response.content)

    return f"/static/audio/{filename}"


# ================= VIDEO =================
def create_luma_video(prompt):
    try:
        url = f"{LUMA_BASE_URL}/generations"

        headers = {
            "Authorization": f"Bearer {LUMA_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "prompt": prompt,
            "model": "ray-2",
            "resolution": "720p",
            "duration": "5s"
        }

        resp = requests.post(url, headers=headers, json=payload)
        data = resp.json()
        gen_id = data.get("id")

        while True:
            status = requests.get(f"{LUMA_BASE_URL}/generations/{gen_id}", headers=headers).json()
            state = status.get("state")

            if state == "completed":
                video_url = status["assets"]["video"]

                filename = f"video_{int(time.time())}.mp4"
                path = os.path.join("static/videos", filename)

                video_data = requests.get(video_url).content
                with open(path, "wb") as f:
                    f.write(video_data)

                return f"/static/videos/{filename}"

            elif state == "failed":
                return None

            time.sleep(5)

    except:
        return None


# ================= ROUTES =================
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    prompt = request.form.get("prompt", "")

    # Script
    response = mistral_client.chat.completions.create(
        model="mistral-large-latest",
        messages=[{"role": "user", "content": prompt}]
    )
    script = response.choices[0].message.content

    # Image
    image = generate_stability_image(prompt)

    # Audio
    audio = generate_audio(script)

    # Video
    video = create_luma_video(prompt)

    # ✅ ONLY FIXED PART (NO ERROR STOP)
    if not video:
        print("⚠️ Video failed, continuing...")

    return jsonify({
        "success": True,
        "script": script,
        "background": image,
        "audio": audio,
        "video": video
    })


# ================= RUN =================
if __name__ == "__main__":
    print("🌐 Server: http://localhost:5000")
    app.run(debug=True)