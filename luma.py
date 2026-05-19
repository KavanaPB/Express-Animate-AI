import requests
import time
import json
import os
from datetime import datetime

# 🔴 PUT YOUR API KEY HERE
LUMA_API_KEY = "api key "

BASE_URL = "https://api.lumalabs.ai/dream-machine/v1"

# ======================
# ✅ TEST CONNECTION
# ======================
def test_luma_connection():
    print("🔍 Testing Luma API connection...")

    try:
        url = f"{BASE_URL}/generations"

        headers = {
            "Authorization": f"Bearer {LUMA_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers)

        print("Status:", response.status_code)

        if response.status_code in [200, 401]:
            print("✅ API reachable")
            return True
        else:
            print("❌ API issue")
            return False

    except Exception as e:
        print("❌ Error:", e)
        return False


# ======================
# ✅ GENERATE VIDEO
# ======================
def generate_luma_video(prompt):
    try:
        url = f"{BASE_URL}/generations"

        headers = {
            "Authorization": f"Bearer {LUMA_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # 🔥 STRONG PROMPT (IMPORTANT)
        enhanced_prompt = f"cinematic, high quality, detailed scene, {prompt}, smooth motion, 4K"

        payload = {
            "prompt": enhanced_prompt,
            "model": "ray-2",
            "resolution": "720p",
            "duration": "5s"
        }

        print("📤 Sending request...")
        response = requests.post(url, headers=headers, json=payload)

        print("📥 Status:", response.status_code)

        if response.status_code != 200:
            print("❌ Request failed:", response.text)
            return None

        result = response.json()
        gen_id = result.get("id")

        if not gen_id:
            print("❌ No generation ID")
            return None

        print("✅ Generation started! ID:", gen_id)

        return wait_for_video(gen_id)

    except Exception as e:
        print("❌ Error:", e)
        return None


# ======================
# ✅ WAIT FOR VIDEO
# ======================
def wait_for_video(gen_id):
    print("⏳ Waiting for video...")

    try:
        while True:
            url = f"{BASE_URL}/generations/{gen_id}"

            headers = {
                "Authorization": f"Bearer {LUMA_API_KEY}",
                "Accept": "application/json"
            }

            response = requests.get(url, headers=headers)
            data = response.json()

            state = data.get("state")
            print("📊 Status:", state)

            if state == "completed":
                video_url = data.get("assets", {}).get("video")

                if not video_url:
                    print("❌ No video URL")
                    return None

                return download_video(video_url, gen_id)

            elif state == "failed":
                print("❌ FULL ERROR:", json.dumps(data, indent=2))
                return None

            time.sleep(8)

    except Exception as e:
        print("❌ Error:", e)
        return None


# ======================
# ✅ DOWNLOAD VIDEO
# ======================
def download_video(video_url, gen_id):
    try:
        print("💾 Downloading video...")

        os.makedirs("luma_videos", exist_ok=True)

        filename = f"luma_{gen_id[:8]}.mp4"
        filepath = os.path.join("luma_videos", filename)

        response = requests.get(video_url, stream=True)

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)

        print("✅ Downloaded:", filepath)
        return filepath

    except Exception as e:
        print("❌ Download error:", e)
        return None


# ======================
# ✅ RETRY SYSTEM (IMPORTANT)
# ======================
def generate_with_retry(prompt, retries=3):
    for i in range(retries):
        print(f"\n🔁 Attempt {i+1}")
        video = generate_luma_video(prompt)
        if video:
            return video

    print("❌ All attempts failed")
    return None


# ======================
# ✅ MAIN
# ======================
if __name__ == "__main__":
    print("🎬 LUMA VIDEO GENERATOR")

    if not test_luma_connection():
        print("❌ Fix API key first")
        exit()

    prompt = input("\n🎯 Enter prompt: ").strip()

    if not prompt:
        prompt = "A girl walking in a magical forest with cinematic lighting"

    generate_with_retry(prompt)