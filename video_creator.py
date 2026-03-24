import os, requests, json, random
from groq import Groq
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips

# الإعدادات من GitHub Secrets
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

client = Groq(api_key=GROQ_API_KEY)

def get_dynamic_story():
    """توليد قصة تقنية مبتكرة باستخدام AI"""
    prompt = """
    Think of a shocking or mysterious true story from tech history.
    Write a 28-second viral storytelling script for a Reel.
    Return ONLY a JSON format: {"title": "Short Title", "script": "Full Script Content"}
    """
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        data = json.loads(res.choices[0].message.content)
        return data['title'], data['script']
    except Exception as e:
        return "Tech Discovery", "The first ever computer bug was actually a moth found inside a Harvard Mark II computer."

def download_multi_visuals(topic):
    """تحميل 4 مقاطع مختلفة لضمان شروط الربح وتنوع المشاهد"""
    headers = {"Authorization": PEXELS_API_KEY}
    search_query = f"{topic} technology dark cinematic"
    url = f"https://api.pexels.com/videos/search?query={search_query.replace(' ','%20')}&per_page=10"
    
    try:
        res = requests.get(url, headers=headers).json()
        video_files = []
        for i in range(min(4, len(res.get('videos', [])))):
            v_url = res['videos'][i]['video_files'][0]['link']
            filename = f"part_{i}.mp4"
            with open(filename, 'wb') as f:
                f.write(requests.get(v_url).content)
            video_files.append(filename)
        return video_files
    except:
        return []

def create_pro_reel(title, script, video_files):
    """مونتاج الفيديو: دمج الصوت مع المشاهد المتقطعة"""
    # 1. توليد الصوت
    tts = gTTS(text=script, lang='en')
    tts.save("voice.mp3")
    audio = AudioFileClip("voice.mp3")
    
    # 2. تجميع المشاهد (تغيير المشهد كل 7 ثواني)
    clips = []
    for file in video_files:
        if os.path.exists(file):
            clip = VideoFileClip(file).subclip(0, 7).resize(height=1920).crop(x_center=540, width=1080)
            clips.append(clip)
    
    if not clips: return False
    
    main_video = concatenate_videoclips(clips).set_duration(audio.duration)
    
    # 3. النصوص (العنوان)
    title_overlay = TextClip(
        title.upper(), 
        fontsize=75, 
        color='yellow', 
        font='Arial-Bold', 
        method='caption', 
        size=(900, None),
        bg_color='black'
    ).set_position('center').set_duration(6).set_opacity(0.85)
    
    # 4. العلامة المائية
    brand = TextClip("TECH MYSTERIES", fontsize=40, color='white', font='Arial-Bold')
    brand = brand.set_position(('center', 1700)).set_duration(audio.duration).set_opacity(0.4)
    
    # دمج النهائي
    final = CompositeVideoClip([main_video, title_overlay, brand]).set_audio(audio)
    final.write_videofile("final_reel.mp4", fps=24, codec="libx264", audio_codec="aac")
    return True

def upload_to_facebook(title):
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/videos"
    try:
        with open('final_reel.mp4', 'rb') as f:
            payload = {
                'description': f"🕵️‍♂️ Tech Mystery: {title}\n\n#Storytelling #TechHistory #Innovation #AI #TechSecrets",
                'access_token': FB_PAGE_ACCESS_TOKEN
            }
            res = requests.post(url, data=payload, files={'source': f}).json()
            return res
    except:
        return {"error": "Upload failed"}

if __name__ == "__main__":
    print("🎬 Starting Pro Video Engine (No Music Edition)...")
    title, script = get_dynamic_story()
    videos = download_multi_visuals(title)
    
    if videos and create_pro_reel(title, script, videos):
        print("🚀 Uploading to Facebook...")
        result = upload_to_facebook(title)
        print(f"Result: {result}")
    else:
        print("❌ Error: Could not create video.")
