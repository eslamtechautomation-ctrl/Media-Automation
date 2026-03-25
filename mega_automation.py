import os, requests, json, re, random
from groq import Groq
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
import proglog
import PIL.Image

# حل مشكلة ANTIALIAS في النسخ الجديدة من Pillow
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

# كتم اللوجات لمنع تداخل العمليات
proglog.default_bar_logger = lambda *args, **kwargs: None

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

client = Groq(api_key=GROQ_API_KEY)

# قائمة تطبيقاتك الـ 20
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
    """معالجة الـ KeyError بذكاء"""
    prompt = f"Return ONLY JSON: {{\"post\": \"viral post for {app['name']}\", \"script\": \"10 sec script\"}}"
    try:
        res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
        match = re.search(r'\{.*\}', res.choices[0].message.content, re.DOTALL)
        if match:
            data = json.loads(match.group())
            p = data.get('post') or data.get('facebook_post') or f"Get {app['name']} now!"
            s = data.get('script') or data.get('video_script') or f"Check out {app['name']}."
            return {"post": p, "script": s}
    except: pass
    return {"post": f"Top App: {app['name']}", "script": f"Download {app['name']} today."}

def make_video(app_name, script):
    """حل مشكلة المونتاج والنصوص"""
    headers = {"Authorization": PEXELS_API_KEY}
    v_data = requests.get("https://api.pexels.com/videos/search?query=technology&per_page=1", headers=headers).json()
    v_url = v_data['videos'][0]['video_files'][0]['link']
    with open("v.mp4", "wb") as f: f.write(requests.get(v_url).content)
    
    gTTS(text=script, lang='en').save("a.mp3")
    audio = AudioFileClip("a.mp3")
    
    # كروب للفيديو ليكون طولي (9:16)
    clip = VideoFileClip("v.mp4").subclip(0, min(audio.duration, 12)).resize(height=1920).crop(x_center=540, width=1080)
    
    try:
        txt = TextClip(app_name.upper(), fontsize=70, color='yellow', font='Arial-Bold', bg_color='black', size=(900, 250)).set_position('center').set_duration(audio.duration)
        final = CompositeVideoClip([clip, txt]).set_audio(audio)
    except:
        final = clip.set_audio(audio)
        
    final.write_videofile("out.mp4", fps=24, codec="libx264", audio_codec="aac", threads=2)
    return "out.mp4"

def upload_fb(path, msg):
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/videos"
    with open(path, 'rb') as f:
        return requests.post(url, data={'description': msg, 'access_token': FB_PAGE_ACCESS_TOKEN}, files={'source': f}).json()

if __name__ == "__main__":
    app = get_next_app()
    info = get_content(app)
    video = make_video(app['name'], info['script'])
    result = upload_fb(video, f"{info['post']}\n\n📥 {app['url']}")
    print(result)
