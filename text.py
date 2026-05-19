import time
import requests
import os
import replicate

# ======================
# CONFIGURATION
# ======================
LUMA_API_KEY = "API key"
ELEVENLABS_API_KEY = ""  # Replace with your ElevenLabs key
REPLICATE_API_TOKEN = ""
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

BASE_URL = "https://api.lumalabs.ai/dream-machine/v1"

# ======================
# STEP 1: Generate video with Luma AI
# ======================
def create_luma_video(prompt: str, model: str = "ray-2", resolution: str = "720p"):
    url = f"{BASE_URL}/generations"
    headers = {
        "Authorization": f"Bearer {LUMA_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "prompt": prompt,
        "model": model,
        "resolution": resolution,
    }

    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()

def get_generation_status(gen_id: str):
    url = f"{BASE_URL}/generations/{gen_id}"
    headers = {"Authorization": f"Bearer {LUMA_API_KEY}", "Accept": "application/json"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

def download_video(url: str, filepath: str):
    resp = requests.get(url, stream=True)
    resp.raise_for_status()
    with open(filepath, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

def text_to_video(prompt: str):
    gen = create_luma_video(prompt)
    gen_id = gen.get("id")
    print("Generation started. ID:", gen_id)

    while True:
        status = get_generation_status(gen_id)
        state = status.get("state")
        print("Current state:", state)
        if state == "completed":
            break
        elif state == "failed":
            raise RuntimeError("Generation failed: " + str(status.get("failure_reason")))
        time.sleep(5)

    assets = status.get("assets", {})
    video_url = assets.get("video")
    if not video_url:
        raise RuntimeError("No video URL returned")

    print("✅ Video ready!")
    print("Video URL:", video_url)
    download_video(video_url, f"{gen_id}.mp4")
    print("Downloaded video to", f"{gen_id}.mp4")
    return video_url

# ======================
# STEP 2: Generate speech with ElevenLabs (auto pick any available voice)
# ======================
def generate_audio(prompt_text):
    headers = {"xi-api-key": ELEVENLABS_API_KEY}
    resp = requests.get("https://api.elevenlabs.io/v1/voices", headers=headers)
    resp.raise_for_status()
    voices = resp.json()["voices"]

    if not voices:
        raise RuntimeError("No voices available in ElevenLabs account.")

    voice_id = voices[0]["voice_id"]
    print(f"Using ElevenLabs voice: {voices[0]['name']} ({voice_id})")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json"
    }
    payload = {"text": prompt_text, "voice_settings": {"stability": 0.7, "similarity_boost": 0.7}}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    audio_file = "speech.mp3"
    with open(audio_file, "wb") as f:
        f.write(response.content)
    print(f"Audio saved: {audio_file}")
    return audio_file

# ======================
# STEP 3: Upload audio to tmpfiles.org
# ======================
def upload_audio(audio_file):
    with open(audio_file, "rb") as f:
        resp = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f})
    resp.raise_for_status()
    url = resp.json()["data"]["url"]
    download_url = url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
    print("Uploaded audio URL:", download_url)
    return download_url

# ======================
# STEP 4: Lip sync with Replicate Wav2Lip
# ======================
def lip_sync(video_url, audio_url):
    output = replicate.run(
        "abhishek/wav2lip:2b5baf5b5eae54dbe3ed9c5c7489829fc952406b8e1d50e3b3c3bcbd869629a0",
        input={"face": video_url, "audio": audio_url}
    )
    return output

# ======================
# MAIN SCRIPT
# ======================
if __name__ == "__main__":
    prompt_text = input("Enter your prompt for the video: ")

    # Step 1: Generate video
    video_url = text_to_video(prompt_text)

    # Step 2: Generate audio
    audio_file = generate_audio(prompt_text)

    # Step 3: Upload audio
    audio_url = upload_audio(audio_file)

    # Step 4: Lip sync
    synced_video_url = lip_sync(video_url, audio_url)
    print("✅ Lip-synced video URL:", synced_video_url)
