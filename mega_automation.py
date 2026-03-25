import os, requests, json, re
from groq import Groq
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
import PIL.Image

# حل مشكلة Pillow الجديدة
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

# كتم أي تسجيل عمليات قد يسبب فشل الأكشن
os.environ["PROGLOG_DISABLE_BAR"] = "True"

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

client = Groq(api_key=GROQ_API_KEY)

# قائمة تطبيقاتك
APPS = [
    {"name": "Smart IPTV Player", "url": "https://play.google.com/store/apps/details?id=asd.iptvplayer"},
    {"name": "Injury Lawyer Guide", "url": "https://play.google.com/store/apps/details?id=injurylawyerguide.aplizrc"},
    {"name": "Design AI 2", "url": "https://play.google.com/store/apps/details?id=design.ai2"},
    {"name": "Fast Lite Web Browser", "url": "https://play.google.com/store/apps/details?id=fast.litewebbrowser"},
    {"name": "Al Hilal Fans", "url": "https://play.google.com/store/apps/details?id=al.hilalfans"},
    {"name": "Quick ToolsHub", "url": "https://play.google.com/store/apps/details?id=quick.toolshub"},
    {"name": "Smart IPTV Viewer", "url": "https://play.google.com/store/apps/details?id=smart.iptvviewer"},
    {"name": "NoteEye", "url": "https://play.google.com/store/apps/details?id=noteeye.ayzi"},
    {"name": "QR App Muq", "url": "https://play.google.com/store/apps/details?id=qr.appmuq"},
    {"name": "K-Cafe Finder", "url": "https://play.google.com/store/apps/details?id=kcafe.finder"},
    {"name": "BPS Productivity", "url": "https://play.google.com/store/apps/details?id=ap3756437.bps"},
    {"name": "TV App Ape", "url": "https://play.google.com/store/apps/details?id=tv.appape"},
    {"name": "QR Scanner 377", "url": "https://play.google.com/store/apps/details?id=qr.scanner377"},
    {"name": "SmartSync Hub", "url": "https://play.google.com/store/apps/details?id=smartsync.hub"},
    {"name": "ConnectSphere", "url": "https://play.google.com/store/apps/details?id=connectsphere.aczh"},
    {"name": "Insurance App Guide", "url": "https://play.google.com/store/apps/details?id=insurance.aplicnem"},
    {"name": "Digital CV Share", "url": "https://play.google.com/store/apps/details?id=digital.cvshare"},
    {"name": "Toolify Daily Monitor", "url": "https://play.google.com/store/apps/details?id=toolify.dailytoolsusagemonitor"},
    {"name": "DHO Productivity", "url": "https://play.google.com/store/apps/details?id=app3514831.dho"},
    {"name": "ASD 26", "url": "https://play.google.com/store/apps/details?id=com.eslamegyp.asd26"}
]

def get_next_app():
    ptr_file = "app_pointer.json"
    idx = 0
    if os.path.exists(ptr_file):
        try:
            with open(ptr_file, 'r') as f:
                idx = (json.load(f).get("idx", 0) + 1) % len(APPS)
        except: idx = 0
    with open(ptr_file, 'w') as f:
        json.dump({"idx": idx}, f)
    return APPS[idx]

def get_content(app):
    """تجنب الـ KeyError نهائياً"""
    prompt = f"Return ONLY JSON: {{\"post\": \"post text for {app['name']}\", \"script\": \"video script\"}}"
    try:
        res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
        data = json.loads(re.search(r'\{.*\}', res.choices[0].message.content, re.DOTALL).group())
        return {
            "post": data.get('post', data.get('facebook_post', f"Check {app['name']}")),
            "script": data.get('script', data.get('video_script', f"Download {app['name']}"))
        }
    except:
        return {"post": f"Amazing app: {app['name']}", "script": f"Try {app['name']} today."}

def make_video(app_name, script):
    """إنتاج الفيديو بدون Logger"""
    v_url = requests.get(f"https://api.pexels.com/videos/search?query=tech&per_page=1", headers={"Authorization": PEXELS_API_KEY}).json()['videos'][0]['video_files'][0]['link']
    with open("v.mp4", "wb") as f: f.write(requests.get(v_url).content)
    
    gTTS(text=script, lang='en').save("a.mp3")
    audio = AudioFileClip("a.mp3")
    clip = VideoFileClip("v.mp4").subclip(0, min(audio.duration, 10)).resize(height=1920).crop(x_center=540, width=1080)
    
    try:
        txt = TextClip(app_name.upper(), fontsize=60, color='white', font='Arial-Bold', bg_color='blue', size=(800, 200)).set_position('center').set_duration(audio.duration)
        final = CompositeVideoClip([clip, txt]).set_audio(audio)
    except:
        final = clip.set_audio(audio)
    
    # استخدام logger=None هو السر في حل مشكلة 'NoneType' object is not callable
    final.write_videofile("promo.mp4", fps=24, codec="libx264", audio_codec="aac", logger=None)
    return "promo.mp4"

def upload(path, msg):
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/videos"
    with open(path, 'rb') as f:
        return requests.post(url, data={'description': msg, 'access_token': FB_PAGE_ACCESS_TOKEN}, files={'source': f}).json()

if __name__ == "__main__":
    app = get_next_app()
    info = get_content(app)
    v_path = make_video(app['name'], info['script'])
    print(upload(v_path, f"{info['post']}\n\n📥 {app['url']}"))
