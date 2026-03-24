import os, requests, json, random
from groq import Groq
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips

# جلب المفاتيح من GitHub Secrets
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

client = Groq(api_key=GROQ_API_KEY)

def get_dynamic_story():
    """توليد قصة تقنية ذكية جداً باستخدام Llama 3"""
    prompt = """
    Think of a mysterious or mind-blowing true story from tech history (Apple, Bitcoin, NASA, Hacking).
    Write a 28-second viral script for a Facebook Reel. 
    Format it as JSON: {"title": "Short Catchy Title", "script": "The full dramatic script"}
    Return ONLY JSON.
    """
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        data = json.loads(res.choices[0].message.content)
        return data['title'], data['script']
    except:
        return "The First Bug", "In 1947, engineers found a real moth inside a computer. That's why we call them bugs!"

def download_multi_visuals(topic):
    """تحميل 4 مقاطع مختلفة عشان الفيديو يبقى 'أصلي' للفيس بوك"""
    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/videos/search?query={topic.replace(' ','%20')}%20technology&per_page=10"
    try:
        res = requests.get(url, headers=headers).json()
        files = []
        for i in range(min(4, len(res.get('videos', [])))):
            v_url = res['videos'][i]['video_files'][0]['link']
            path = f"part_{i}.mp4"
            with open(path, 'wb') as f: f.write(requests.get(v_url).content)
            files.append(path)
        return files
    except: return []

def create_video(title, script, video_files):
    # 1. الصوت
    tts = gTTS(text=script, lang='en')
    tts.save("voice.mp3")
    audio = AudioFileClip("voice.mp3")
    
    # 2. المونتاج (مشاهد متغيرة كل 7 ثواني)
    clips = []
    for f in video_files:
        if os.path.exists(f):
            c = VideoFileClip(f).subclip(0, 7).resize(height=1920).crop(x_center=540, width=1080)
            clips.append(c)
    
    if not clips: return False
    
    main_v = concatenate_videoclips(clips).set_duration(audio.duration)
    
    # 3. النص على الشاشة (بشكل احترافي)
    txt = TextClip(title.upper(), fontsize=70, color='yellow', font='Arial-Bold', 
                   bg_color='black', method='caption', size=(900, None))
    txt = txt.set_position('center').set_duration(6).set_opacity(0.8)
    
    # 4. دمج وحفظ
    final = CompositeVideoClip([main_v, txt]).set_audio(audio)
    final.write_videofile("final_reel.mp4", fps=24, codec="libx264", audio_codec="aac")
    return True

def post_to_fb(title):
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/videos"
    try:
        with open('final_reel.mp4', 'rb') as f:
            payload = {'description': f"🕵️‍♂️ {title} #TechSecrets #AI #Innovation", 'access_token': FB_PAGE_ACCESS_TOKEN}
            return requests.post(url, data=payload, files={'source': f}).json()
    except: return {"error": "upload failed"}

if __name__ == "__main__":
    print("🔥 Starting Pro System...")
    title, script = get_dynamic_story()
    videos = download_multi_visuals(title)
    if videos and create_video(title, script, videos):
        print("🚀 Uploading...")
        res = post_to_fb(title)
        print(f"Result: {res}")
