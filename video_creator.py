import os
import requests
import feedparser
import json
import random
import time
from groq import Groq
from gtts import gTTS
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
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except: return []
    return []

def save_memory(trend_title):
    memory = load_memory()
    memory.append(trend_title)
    # الاحتفاظ بآخر 100 تريند بس لتوفير المساحة
    if len(memory) > 100: memory.pop(0)
    with open(DB_FILE, "w") as f:
        json.dump(memory, f)

def get_google_trend():
    # سحب التريندات اليومية من أمريكا (مصدر الـ Tech العالمي)
    trends_url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
    feed = feedparser.parse(trends_url)
    memory = load_memory()
    
    for entry in feed.entries:
        if entry.title not in memory:
            return entry.title
    return None

def get_deep_tech_script(trend_topic):
    # الـ Prompt الجديد: طلب تحليل عميق ومعلومة حقيقية
    prompt = f"""
    Topic: {trend_topic}
    Task: Write a deep, educational 25-second viral video script for a Facebook Reel.
    Structure:
    1. Hook (Start with a surprising fact about this topic).
    2. Deep Tech Fact (Provide real, detailed info - 'Did you know...').
    3. CTA (Call to action).
    Return ONLY the English script text, no formatting.
    """
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content

def download_bg_video(query):
    # البحث عن فيديو ذي صلة بالتريند لزيادة الجودة البصرية
    search_query = query.replace(" ", "%20")
    url = f"https://api.pexels.com/videos/search?query={search_query}%20technology&per_page=10"
    headers = {"Authorization": PEXELS_API_KEY}
    try:
        res = requests.get(url, headers=headers).json()
        if res['videos']:
            video_data = random.choice(res['videos'])
            video_url = video_data['video_files'][0]['link']
            with open("bg_video.mp4", 'wb') as f:
                f.write(requests.get(video_url).content)
            return True
    except: pass
    
    # فيديو احتياطي لو البحث فشل
    url_backup = "https://api.pexels.com/videos/search?query=futuristic%20technology&per_page=1"
    res_backup = requests.get(url_backup, headers=headers).json()
    video_url_backup = res_backup['videos'][0]['video_files'][0]['link']
    with open("bg_video.mp4", 'wb') as f:
        f.write(requests.get(video_url_backup).content)
    return False

def create_reel(script_text, trend_title):
    # 1. الصوت
    tts = gTTS(text=script_text, lang='en')
    tts.save("voice.mp3")
    
    # 2. الفيديو (30 ثانية ليكون "دسم")
    video_clip = VideoFileClip("bg_video.mp4").subclip(0, 30).resize(width=1080)
    audio_clip = AudioFileClip("voice.mp3")
    
    # 3. النص الجاذب (اسم التريند بخط كبير فوق)
    title_clip = TextClip(trend_title.upper(), fontsize=80, color='white', font='Arial-Bold', bg_color='black')
    title_clip = title_clip.set_position(('center', 100)).set_duration(30).set_opacity(0.8)
    
    # 4. الشعار
    watermark = TextClip("Trend Tech", fontsize=60, color='white', font='Arial-Bold')
    watermark = watermark.set_position(('center', 1750)).set_duration(30).set_opacity(0.5)
    
    # 5. دمج
    final_video = video_clip.set_audio(audio_clip)
    final_video = CompositeVideoClip([final_video, title_clip, watermark])
    final_video.write_videofile("trend_tech_reel.mp4", fps=24, codec="libx264", audio_codec="aac")

def upload_to_fb(trend_title):
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/videos"
    with open('trend_tech_reel.mp4', 'rb') as f:
        files = {'source': f}
        data = {
            'description': f"Deep Dive: {trend_title} 🚀\n\n#TrendTech #TechTrends #AI #Innovation",
            'access_token': FB_PAGE_ACCESS_TOKEN
        }
        return requests.post(url, data=data, files=files).json()

if __name__ == "__main__":
    print("Fetching Top Trend from Google...")
    trend = get_google_trend()
    
    if trend:
        print(f"Working on Deep Dive for: {trend}")
        script = get_deep_tech_script(trend)
        
        print("Downloading relevant background video...")
        download_bg_video(trend)
        
        print("Creating Deep Reel...")
        create_reel(script, trend)
        
        print("Uploading to Facebook...")
        result = upload_to_fb(trend)
        if "id" in result:
            save_memory(trend)
            print("Successfully Posted!")
        else:
            print(f"Upload Failed: {result}")
    else:
        print("No new trends to post.")
