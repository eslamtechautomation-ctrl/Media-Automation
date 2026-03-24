import os
import requests
import json
import random
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
    """توليد فكرة قصة وسيناريو بشكل آلي تماماً"""
    prompt = """
    Think of a mysterious or shocking true story from tech history (e.g., Apple, Bitcoin, Hacking, SpaceTech).
    Write a 28-second viral storytelling script for a Facebook Reel.
    Must include: A mind-blowing hook, 3 punchy facts, and a dramatic ending.
    Language: English.
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
        print(f"Error generating story: {e}")
        return "Tech Secrets", "Did you know that the first computer bug was actually a real moth found inside a machine?"

def download_multi_visuals(topic):
    """تحميل 4 مقاطع فيديو مختلفة لضمان شروط الربح"""
    headers = {"Authorization": PEXELS_API_KEY}
    search_query = f"{topic} technology dark cinematic"
    url = f"https://api.pexels.com/videos/search?query={search_query.replace(' ','%20')}&per_page=10"
    
    try:
        res = requests.get(url, headers=headers).json()
        video_files = []
        # تحميل 4 مقاطع مختلفة لزيادة قيمة المونتاج
        for i in range(min(4, len(res['videos']))):
            v_url = res['videos'][i]['video_files'][0]['link']
            filename = f"part_{i}.mp4"
            with open(filename, 'wb') as f:
                f.write(requests.get(v_url).content)
            video_files.append(filename)
        return video_files
    except Exception as e:
        print(f"Error downloading visuals: {e}")
        return []

def create_pro_reel(title, script, video_files):
    """مونتاج احترافي بمشاهد متعددة وعناوين واضحة"""
    # 1. توليد الصوت
    tts = gTTS(text=script, lang='en')
    tts.save("voice.mp3")
    audio = AudioFileClip("voice.mp3")
    
    # 2. معالجة المشاهد (تغيير المشهد كل 7 ثواني تقريباً)
    clips = []
    for file in video_files:
        if os.path.exists(file):
            # ضبط المقاس ليكون Reels (9:16)
            clip = VideoFileClip(file).subclip(0, 7).resize(height=1920).crop(x_center=540, width=1080)
            clips.append(clip)
    
    if not clips: return False
    
    main_video = concatenate_videoclips(clips).set_duration(audio.duration)
    
    # 3. إضافة النصوص (العنوان في المنتصف بخلفية سوداء)
    title_overlay = TextClip(
        title.upper(), 
        fontsize=70, 
        color='yellow', 
        font='Arial-Bold', 
        method='caption', 
        size=(900, None),
        bg_color='black'
    ).set_position('center').set_duration(6).set_opacity(0.85).crossfadeout(1)
    
    # 4. العلامة المائية في الأسفل
    brand = TextClip("TECH MYSTERIES", fontsize=40, color='white', font='Arial-Bold')
    brand = brand.set_position(('center', 1700)).set_duration(audio.duration).set_opacity(0.4)
    
    # دمج الصوت والصورة
    final = CompositeVideoClip([main_video, title_overlay, brand]).set_audio(audio)
    final.write_videofile("final_reel.mp4", fps=24, codec="libx264", audio_codec="aac")
    return True

def upload_to_facebook(title):
    """رفع الفيديو النهائي لصفحة فيسبوك"""
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/videos"
    try:
        with open('final_reel.mp4', 'rb') as f:
            payload = {
                'description': f"🕵️‍♂️ Tech Mystery: {title}\n\n#Storytelling #TechHistory #Innovation #AI #TechSecrets",
                'access_token': FB_PAGE_ACCESS_TOKEN
            }
            res = requests.post(url, data=payload, files={'source': f}).json()
            return res
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("🎬 Starting AI Story Engine...")
    
    # 1. الحصول على القصة
    story_title, story_script = get_dynamic_story()
    print(f"📖 Story Topic: {story_title}")
    
    # 2. تحميل المشاهد (تجنباً لخطأ الـ Logs السابق)
    print("📥 Fetching multi-scene visuals...")
    videos = download_multi_visuals(story_title)
    
    if videos:
        # 3. المونتاج
        print("✂️ Assembling cinematic reel...")
        if create_pro_reel(story_title, story_script, videos):
            # 4. الرفع
            print("🚀 Uploading to Facebook...")
            result = upload_to_facebook(story_title)
            if "id" in result:
                print(f"✅ Video Published Successfully! ID: {result['id']}")
            else:
                print(f"❌ Upload Error: {result}")
    else:
        print("❌ Script stopped: No visuals found.")
