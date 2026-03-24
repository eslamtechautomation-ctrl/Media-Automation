import os, requests, json, random
from groq import Groq
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, CompositeAudioClip

# الإعدادات
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

client = Groq(api_key=GROQ_API_KEY)

def get_dynamic_story():
    prompt = """
    Think of a mysterious or shocking true story from tech history.
    Write a 28-second viral storytelling script for a Reel.
    Return ONLY a JSON format: {"title": "Short Title", "script": "Full Script Content"}
    """
    res = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"}
    )
    data = json.loads(res.choices[0].message.content)
    return data['title'], data['script']

def download_music():
    """تحميل موسيقى خلفية مجانية إذا لم تكن موجودة"""
    music_path = "suspense.mp3"
    if not os.path.exists(music_path):
        print("📥 Downloading background music...")
        # رابط لموسيقى تشويق مجانية (No Copyright)
        url = "https://www.bensound.com/bensound-music/bensound-creepy.mp3" 
        try:
            r = requests.get(url)
            with open(music_path, 'wb') as f:
                f.write(r.content)
        except:
            return None
    return music_path

def download_multi_visuals(topic):
    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/videos/search?query={topic.replace(' ','%20')}%20tech&per_page=5"
    res = requests.get(url, headers=headers).json()
    files = []
    for i in range(min(4, len(res.get('videos', [])))):
        v_url = res['videos'][i]['video_files'][0]['link']
        path = f"part_{i}.mp4"
        with open(path, 'wb') as f: f.write(requests.get(v_url).content)
        files.append(path)
    return files

def create_pro_reel(title, script, video_parts):
    # 1. صوت المعلق
    tts = gTTS(text=script, lang='en')
    tts.save("voice.mp3")
    voice = AudioFileClip("voice.mp3")
    
    # 2. دمج الموسيقى
    music_file = download_music()
    if music_file:
        bg_music = AudioFileClip(music_file).volumex(0.15).set_duration(voice.duration)
        final_audio = CompositeAudioClip([voice, bg_music])
    else:
        final_audio = voice

    # 3. المونتاج (تغيير المشاهد)
    clips = [VideoFileClip(p).subclip(0, 7).resize(height=1920).crop(x_center=540, width=1080) for p in video_parts if os.path.exists(p)]
    main_video = concatenate_videoclips(clips).set_duration(voice.duration)
    
    # 4. العنوان
    txt = TextClip(title.upper(), fontsize=70, color='yellow', font='Arial-Bold', bg_color='black', method='caption', size=(900, None))
    txt = txt.set_position('center').set_duration(6).set_opacity(0.85)
    
    final = CompositeVideoClip([main_video, txt]).set_audio(final_audio)
    final.write_videofile("final_reel.mp4", fps=24, codec="libx264", audio_codec="aac")

def upload_to_facebook(title):
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/videos"
    with open('final_reel.mp4', 'rb') as f:
        payload = {'description': f"🎬 {title} #TechMysteries #AI #Stories", 'access_token': FB_PAGE_ACCESS_TOKEN}
        return requests.post(url, data=payload, files={'source': f}).json()

if __name__ == "__main__":
    print("🚀 Starting Professional Video Creator...")
    t, s = get_dynamic_story()
    v = download_multi_visuals(t)
    if v:
        create_pro_reel(t, s, v)
        res = upload_to_facebook(t)
        print(f"Done! FB ID: {res.get('id')}")
