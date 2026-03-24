import os
import requests
import feedparser
import json
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
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return []

def save_memory(link):
    memory = load_memory()
    memory.append(link)
    with open(DB_FILE, "w") as f:
        json.dump(memory, f)

def get_arabic_script(title):
    # نطلب من جروق تلخيص الخبر بالعربي بأسلوب تريند
    prompt = f"Translate and summarize this tech news into a catchy 20-second Arabic script for a Reel: {title}. Use professional yet engaging Arabic. Return ONLY the Arabic text."
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content

def download_bg_video():
    url = "https://api.pexels.com/videos/search?query=technology&per_page=15" # سحبنا 15 فيديو لنختار عشوائي
    headers = {"Authorization": PEXELS_API_KEY}
    res = requests.get(url, headers=headers).json()
    import random
    video_data = random.choice(res['videos'])
    video_url = video_data['video_files'][0]['link']
    with open("bg_video.mp4", 'wb') as f:
        f.write(requests.get(video_url).content)

def create_reel(arabic_text):
    # 1. الصوت (عربي)
    tts = gTTS(text=arabic_text, lang='ar')
    tts.save("voice.mp3")
    
    # 2. المونتاج (25 ثانية)
    video_clip = VideoFileClip("bg_video.mp4").subclip(0, 25).resize(width=1080)
    audio_clip = AudioFileClip("voice.mp3")
    
    # 3. الشعار
    watermark = TextClip("Trend Tech", fontsize=50, color='white', font='Arial-Bold')
    watermark = watermark.set_pos(('center', 0.85, 'relative')).set_duration(25).set_opacity(0.6)
    
    final_video = video_clip.set_audio(audio_clip)
    final_video = CompositeVideoClip([final_video, watermark])
    final_video.write_videofile("trend_tech_reel.mp4", fps=24, codec="libx264")

def upload_to_fb(title):
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/videos"
    files = {'source': open('trend_tech_reel.mp4', 'rb')}
    data = {
        'description': f"{title}\n\n#TrendTech #اخبار_التقنية #ذكاء_اصطناعي",
        'access_token': FB_PAGE_ACCESS_TOKEN
    }
    return requests.post(url, data=data, files=files).json()

if __name__ == "__main__":
    feed = feedparser.parse("https://familytvr.blogspot.com/feeds/posts/default?alt=rss")
    memory = load_memory()
    
    selected_entry = None
    for entry in feed.entries:
        if entry.link not in memory:
            selected_entry = entry
            break
            
    if selected_entry:
        print(f"New News Found: {selected_entry.title}")
        ar_script = get_arabic_script(selected_entry.title)
        download_bg_video()
        create_reel(ar_script)
        
        result = upload_to_fb(selected_entry.title)
        if "id" in result:
            save_memory(selected_entry.link)
            print("Successfully Posted!")
    else:
        print("Everything is up to date.")
