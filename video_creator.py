import os
import requests
import json
import random
from groq import Groq
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips

# الإعدادات - تأكد من وجودها في Secrets GitHub
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

client = Groq(api_key=GROQ_API_KEY)

def get_dynamic_story():
    """توليد فكرة قصة وسيناريو بشكل آلي تماماً"""
    prompt = """
    Think of a mysterious, shocking, or inspiring true story from tech history (Apple, Google, Hacking, AI, etc.).
    Then, write a 28-second viral storytelling script for a Reel.
    Structure: Mind-blowing hook, punchy facts, dramatic ending.
    Language: English.
    Return ONLY a JSON format like this: 
    {"title": "The short title", "script": "The full script text"}
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
    """تحميل عدة مقاطع لضمان جودة المونتاج وقبول الربح"""
    headers = {"Authorization": PEXELS_API_KEY}
    # البحث عن فيديوهات مرتبطة بالموضوع أو تكنولوجيا غامضة بشكل عام
    search_query = f"{topic} technology dark"
    url = f"https://api.pexels.com/videos/search?query={search_query.replace(' ','%20')}&per_page=10"
    
    try:
        res = requests.get(url, headers=headers).json()
        video_files = []
        # هناخد 4 مقاطع مختلفة
        for i in range(min(4, len(res['videos']))):
            v_url = res['videos'][i]['video_files'][0]['link']
            filename = f"part_{i}.mp4"
            with open(filename, 'wb') as f:
                f.write(requests.get(v_url).content)
            video_files.append(filename)
        return video_files
    except Exception as e:
        print(f"Error downloading videos: {e}")
        return []

def create_pro_reel(title, script, video_files):
    """مونتاج احترافي بمشاهد متعددة وعناوين واضحة"""
    # 1. توليد الصوت
    tts = gTTS(text=script, lang='en')
    tts.save("voice.mp3")
    audio = AudioFileClip("voice.mp3")
    
    # 2. معالجة المشاهد (تغيير كل 7 ثواني)
    clips = []
    for file in video_files:
        if os.path.exists(file):
            # ضبط المقاس ليكون Reels (9:16)
            clip = VideoFileClip(file).subclip(0, 7).resize(height=1920).crop(x_center=540, width=1080)
            clips.append(clip)
    
    if not clips: return False
    
    main_video = concatenate_videoclips(clips).set_duration(audio.duration)
    
    # 3. إضافة النصوص (العنوان)
    title_overlay = TextClip(
        title.upper(), 
        fontsize=75, 
        color='yellow', 
        font='Arial-Bold', 
        method='caption', 
        size=(900, None),
        bg_color='black'
    ).set_position('center').set_duration(6).set_opacity(0.9).crossfadeout(1)
    
    # 4. العلامة المائية
    brand = TextClip("TECH MYSTERIES", fontsize=40, color='white', font='Arial-Bold')
    brand = brand.set_position(('center', 1750)).set_duration(audio.duration).set_opacity(0.4)
    
    # دمج الكل
    final = CompositeVideoClip([main_video, title_overlay, brand]).set_audio(audio)
    final.write_videofile("final_reel.mp4", fps=24, codec="libx264", audio_codec="aac")
    return True

def upload_to_facebook(title):
    """رفع الفيديو لفيسبوك"""
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/videos"
    try:
        with open('final_reel.mp4', 'rb') as f:
            payload = {
                'description': f"🎬 {title}\n\n#TechSecrets #Mysteries #Innovation #AI #Storytelling",
                'access_token': FB_PAGE_ACCESS_TOKEN
            }
            res = requests.post(url, data=payload, files={'source': f}).json()
            return res
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("🧠 Thinking of a mysterious story...")
    story_title, story_script = get_dynamic_story()
    print(f"📖 Title: {story_title}")
    
    print("📥 Downloading multi-scene visuals...")
    videos = download_multi_visuals(story_title)
    
    if videos:
        print("🎬 Editing your professional reel...")
        if create_pro_reel(story_title, story_script, videos):
            print("🚀 Uploading to Facebook...")
            result = upload_to_facebook(story_title)
            if "id" in result:
                print(f"✅ Success! Video ID: {result['id']}")
            else:
                print(f"❌ Failed to upload: {result}")
    else:
        print("❌ No videos found to download.")
