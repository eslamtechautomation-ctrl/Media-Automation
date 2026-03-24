import os, requests, json, random, re
from groq import Groq
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips

# الإعدادات
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

client = Groq(api_key=GROQ_API_KEY)

def get_dynamic_story():
    prompt = """
    Think of a mysterious true story from tech history.
    Write a 28-second viral script for a Reel. 
    Return ONLY a JSON object: {"title": "Title Here", "script": "Script Here"}
    Do not add any text before or after the JSON.
    """
    try:
        res = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile"
        )
        content = res.choices[0].message.content
        # تنظيف الرد من أي علامات Markdown قد تسبب الخطأ اللي ظهر في الصورة
        clean_json = re.search(r'\{.*\}', content, re.DOTALL).group()
        data = json.loads(clean_json)
        return data['title'], data['script']
    except Exception as e:
        print(f"JSON Fix applied due to error: {e}")
        return "Tech Secret", "Did you know that the first computer bug was a real moth?"

def download_multi_visuals(topic):
    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/videos/search?query={topic.replace(' ','%20')}&per_page=5"
    try:
        res = requests.get(url, headers=headers).json()
        video_files = []
        for i in range(min(4, len(res.get('videos', [])))):
            v_url = res['videos'][i]['video_files'][0]['link']
            filename = f"part_{i}.mp4"
            with open(filename, 'wb') as f: f.write(requests.get(v_url).content)
            video_files.append(filename)
        return video_files
    except: return []

def create_video(title, script, video_files):
    tts = gTTS(text=script, lang='en')
    tts.save("voice.mp3")
    audio = AudioFileClip("voice.mp3")
    
    clips = []
    for f in video_files:
        if os.path.exists(f):
            c = VideoFileClip(f).subclip(0, 7).resize(height=1920).crop(x_center=540, width=1080)
            clips.append(c)
    
    if not clips: return False
    
    main_v = concatenate_videoclips(clips).set_duration(audio.duration)
    txt = TextClip(title.upper(), fontsize=70, color='yellow', font='Arial-Bold', bg_color='black', method='caption', size=(900, None))
    txt = txt.set_position('center').set_duration(6).set_opacity(0.8)
    
    final = CompositeVideoClip([main_v, txt]).set_audio(audio)
    final.write_videofile("final_reel.mp4", fps=24, codec="libx264", audio_codec="aac")
    return True

def post_to_fb(title):
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/videos"
    try:
        with open('final_reel.mp4', 'rb') as f:
            payload = {'description': f"🕵️‍♂️ {title} #TechSecrets #AI", 'access_token': FB_PAGE_ACCESS_TOKEN}
            return requests.post(url, data=payload, files={'source': f}).json()
    except: return {"error": "failed"}

if __name__ == "__main__":
    title, script = get_dynamic_story()
    videos = download_multi_visuals(title)
    if videos and create_video(title, script, videos):
        res = post_to_fb(title)
        print(res)
