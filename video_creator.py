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
    # استخدام Groq لعمل SEO وسيناريو قصير
    prompt = f"Write a 15-second viral video script for this tech news: {title}. Keep it punchy and professional. Return only the script text."
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content

def download_bg_video():
    # سحب فيديو خلفية تقني من Pexels
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
    
    # 2. تجهيز الفيديو والمونتاج
# تعديل بسيط لضمان التوافق
    video_clip = VideoFileClip("bg_video.mp4").subclip(0, 15)
    
    # لو الفيديو أصلاً بالعرض، هنخليه بالطول للـ Reels
    final_clip = video_clip.resize(width=1080) # هيظبط العرض والارتفاع هيتظبط تلقائي
audio_clip = AudioFileClip("voice.mp3")
    
    final_video = video_clip.set_audio(audio_clip)
    final_video.write_videofile("trend_tech_reel.mp4", fps=24)

def upload_to_fb_reels():
    # رفع الفيديو لفيسبوك (بصيغة Reels)
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/videos"
    files = {'source': open('trend_tech_reel.mp4', 'rb')}
    data = {
        'description': "Tech Update from Trend Tech! 🚀 #TrendTech #AI #TechNews",
        'access_token': FB_PAGE_ACCESS_TOKEN
    }
    return requests.post(url, data=data, files=files).json()

if __name__ == "__main__":
    # تجربة على آخر خبر
    feed = feedparser.parse("https://familytvr.blogspot.com/feeds/posts/default?alt=rss")
    title = feed.entries[0].title
    
    print("Generating Script with Groq...")
    script = get_video_script(title)
    
    print("Downloading Background Video...")
    download_bg_video()
    
    print("Creating Reel...")
    create_reel(script)
    
    print("Uploading to Facebook...")
    result = upload_to_fb_reels()
    print(f"Final Result: {result}")
