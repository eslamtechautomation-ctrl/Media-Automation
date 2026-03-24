import os
import requests
import feedparser
import json
import random
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

def save_memory(link):
    memory = load_memory()
    memory.append(link)
    with open(DB_FILE, "w") as f:
        json.dump(memory, f)

def get_arabic_script(title):
    prompt = f"Translate and summarize this tech news into a catchy 20-second Arabic script for a Facebook Reel: {title}. Return ONLY the Arabic text."
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content

def download_bg_video():
    url = "https://api.pexels.com/videos/search?query=technology&per_page=15"
    headers = {"Authorization": PEXELS_API_KEY}
    res = requests.get(url, headers=headers).json()
    video_data = random.choice(res['videos'])
    video_url = video_data['video_files'][0]['link']
    with open("bg_video.mp4", 'wb') as f:
        f.write(requests.get(video_url).content)

def create_reel(arabic_text):
    # 1. الصوت
    tts = gTTS(text=arabic_text, lang='ar')
    tts.save("voice.mp3")
    
    # 2. الفيديو (25 ثانية)
    video_clip = VideoFileClip("bg_video.mp4").subclip(0, 25).resize(width=1080)
    audio_clip = AudioFileClip("voice.mp3")
    
    # 3. الشعار (تم تعديل الإحداثيات لحل مشكلة 'relative')
    watermark = TextClip("Trend Tech", fontsize=70, color='white', font='Arial-Bold')
    # وضعه في المنتصف بمسافة 150 بيكسل من الأسفل
    watermark = watermark.set_position(('center', 1700)).set_duration(25).set_opacity(0.5)
    
    # 4. دمج
    final_video = video_clip.set_audio(audio_clip)
    final_video = CompositeVideoClip([final_video, watermark])
    final_video.write_videofile("trend_tech_reel.mp4", fps=24, codec="libx264", audio_codec="aac")

def upload_to_fb(title):
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/videos"
    with open('trend_tech_reel.mp4', 'rb') as f:
        files = {'source': f}
        data = {
            'description': f"{title}\n\n#TrendTech #اخبار_التقنية",
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
        print(f"Working on: {selected_entry.title}")
        ar_script = get_arabic_script(selected_entry.title)
        download_bg_video()
        create_reel(ar_script)
        
        result = upload_to_fb(selected_entry.title)
        if "id" in result:
            save_memory(selected_entry.link)
            print("Done!")
    else:
        print("No new news.")
