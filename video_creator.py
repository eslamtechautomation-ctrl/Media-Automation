import os
import requests
import feedparser
from groq import Groq
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip

# الإعدادات من الـ Secrets
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

client = Groq(api_key=GROQ_API_KEY)

def get_video_script(title):
    prompt = f"Write a very short 15-second tech news summary for: {title}. Keep it simple and engaging for a video script. Return ONLY the text."
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content

def download_bg_video():
    url = "https://api.pexels.com/videos/search?query=technology&per_page=1"
    headers = {"Authorization": PEXELS_API_KEY}
    res = requests.get(url, headers=headers).json()
    video_url = res['videos'][0]['video_files'][0]['link']
    with open("bg_video.mp4", 'wb') as f:
        f.write(requests.get(video_url).content)

def create_reel(script_text):
    # 1. توليد الصوت
    tts = gTTS(text=script_text, lang='en')
    tts.save("voice.mp3")
    
    # 2. تجهيز الفيديو
    video_clip = VideoFileClip("bg_video.mp4").subclip(0, 15).resize(width=1080)
    audio_clip = AudioFileClip("voice.mp3")
    
    # 3. إضافة الشعار (Watermark)
    watermark = TextClip("Trend Tech", fontsize=50, color='white', font='Arial-Bold')
    watermark = watermark.set_pos(('center', 'bottom')).set_duration(15).set_opacity(0.5)
    
    # 4. دمج كل شيء
    final_video = video_clip.set_audio(audio_clip)
    final_video = CompositeVideoClip([final_video, watermark])
    
    final_video.write_videofile("trend_tech_reel.mp4", fps=24, codec="libx264")

def upload_to_fb_reels():
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/videos"
    files = {'source': open('trend_tech_reel.mp4', 'rb')}
    data = {
        'description': "Latest Tech Update! 🚀 #TrendTech #AI #Technology",
        'access_token': FB_PAGE_ACCESS_TOKEN
    }
    return requests.post(url, data=data, files=files).json()

if __name__ == "__main__":
    # سحب خبر من إحدى مدوناتك
    feed_url = "https://familytvr.blogspot.com/feeds/posts/default?alt=rss"
    feed = feedparser.parse(feed_url)
    
    if feed.entries:
        title = feed.entries[0].title
        print(f"Processing: {title}")
        
        script = get_video_script(title)
        download_bg_video()
        create_reel(script)
        
        result = upload_to_fb_reels()
        print(f"Final Result: {result}")
    else:
        print("No news found.")
