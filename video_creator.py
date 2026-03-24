import os
import requests
import json
import random
from groq import Groq
from gtts import gTTS
from pytrends.request import TrendReq
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip

# الإعدادات
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

client = Groq(api_key=GROQ_API_KEY)
DB_FILE = "posted_reels.json"

def load_memory():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return []
    return []

def save_memory(trend):
    memory = load_memory()
    memory.append(trend)
    with open(DB_FILE, "w") as f: json.dump(memory, f)

def get_google_trend():
    try:
        # استخدام pytrends بدلاً من الروابط المتعطلة
        pytrends = TrendReq(hl='en-US', tz=360)
        df = pytrends.trending_searches(pn='united_states')
        memory = load_memory()
        for trend_name in df[0]:
            if trend_name not in memory:
                return trend_name
        return None
    except Exception as e:
        print(f"Trend Error: {e}")
        return None

def get_deep_tech_script(trend_topic):
    prompt = f"Write a viral 25-second educational English script for a tech reel about: {trend_topic}. Hook + Deep Fact + CTA. Return ONLY the script."
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content

def download_bg_video(query):
    url = f"https://api.pexels.com/videos/search?query={query.replace(' ','%20')}%20tech&per_page=5"
    headers = {"Authorization": PEXELS_API_KEY}
    try:
        res = requests.get(url, headers=headers).json()
        video_url = res['videos'][0]['video_files'][0]['link']
        with open("bg_video.mp4", 'wb') as f: f.write(requests.get(video_url).content)
    except:
        # فيديو احتياطي
        res = requests.get("https://api.pexels.com/videos/search?query=technology&per_page=1", headers=headers).json()
        video_url = res['videos'][0]['video_files'][0]['link']
        with open("bg_video.mp4", 'wb') as f: f.write(requests.get(video_url).content)

def create_reel(script_text, trend_title):
    tts = gTTS(text=script_text, lang='en')
    tts.save("voice.mp3")
    
    video_clip = VideoFileClip("bg_video.mp4").subclip(0, 25).resize(width=1080)
    audio_clip = AudioFileClip("voice.mp3")
    
    # عنوان التريند
    title_clip = TextClip(trend_title.upper(), fontsize=70, color='white', font='Arial-Bold', bg_color='black')
    title_clip = title_clip.set_position(('center', 150)).set_duration(25).set_opacity(0.8)
    
    # اللوجو (إحداثيات ثابتة لتجنب ValueError)
    watermark = TextClip("Trend Tech", fontsize=50, color='white', font='Arial-Bold')
    watermark = watermark.set_position(('center', 1700)).set_duration(25).set_opacity(0.5)
    
    final_video = video_clip.set_audio(audio_clip)
    final_video = CompositeVideoClip([final_video, title_clip, watermark])
    final_video.write_videofile("trend_tech_reel.mp4", fps=24, codec="libx264")

def upload_to_fb(title):
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/videos"
    with open('trend_tech_reel.mp4', 'rb') as f:
        data = {'description': f"{title} #TrendTech #Tech", 'access_token': FB_PAGE_ACCESS_TOKEN}
        return requests.post(url, data=data, files={'source': f}).json()

if __name__ == "__main__":
    trend = get_google_trend()
    if trend:
        print(f"Working on: {trend}")
        script = get_deep_tech_script(trend)
        download_bg_video(trend)
        create_reel(script, trend)
        result = upload_to_fb(trend)
        if "id" in result:
            save_memory(trend)
            print("Successfully Posted!")
    else:
        print("No new trends.")
