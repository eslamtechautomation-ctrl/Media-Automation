import os, requests, json, re, random
from groq import Groq
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
import proglog

# كتم اللوجات المزعجة عشان الأكشن ميهنجش
proglog.default_bar_logger = lambda *args, **kwargs: None

# الإعدادات (تأكد من وضعها في GitHub Secrets)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

client = Groq(api_key=GROQ_API_KEY)

# قائمة تطبيقاتك الـ 20
APPS = [
    {"name": "Smart IPTV Player", "url": "https://play.google.com/store/apps/details?id=asd.iptvplayer", "keywords": "iptv, streaming"},
    {"name": "Injury Lawyer Guide", "url": "https://play.google.com/store/apps/details?id=injurylawyerguide.aplizrc", "keywords": "lawyer, legal"},
    {"name": "Design AI 2", "url": "https://play.google.com/store/apps/details?id=design.ai2", "keywords": "interior, design"},
    {"name": "Fast Lite Web Browser", "url": "https://play.google.com/store/apps/details?id=fast.litewebbrowser", "keywords": "browser, fast"},
    {"name": "Al Hilal Fans", "url": "https://play.google.com/store/apps/details?id=al.hilalfans", "keywords": "football, sports"},
    {"name": "Quick ToolsHub", "url": "https://play.google.com/store/apps/details?id=quick.toolshub", "keywords": "tools, utility"},
    {"name": "Smart IPTV Viewer", "url": "https://play.google.com/store/apps/details?id=smart.iptvviewer", "keywords": "iptv, media"},
    {"name": "NoteEye", "url": "https://play.google.com/store/apps/details?id=noteeye.ayzi", "keywords": "notes, daily"},
    {"name": "QR App Muq", "url": "https://play.google.com/store/apps/details?id=qr.appmuq", "keywords": "qr, scanner"},
    {"name": "K-Cafe Finder", "url": "https://play.google.com/store/apps/details?id=kcafe.finder", "keywords": "cafe, map"},
    {"name": "BPS Productivity", "url": "https://play.google.com/store/apps/details?id=ap3756437.bps", "keywords": "business, work"},
    {"name": "TV App Ape", "url": "https://play.google.com/store/apps/details?id=tv.appape", "keywords": "movies, tv"},
    {"name": "QR Scanner 377", "url": "https://play.google.com/store/apps/details?id=qr.scanner377", "keywords": "qr, code"},
    {"name": "SmartSync Hub", "url": "https://play.google.com/store/apps/details?id=smartsync.hub", "keywords": "sync, cloud"},
    {"name": "ConnectSphere", "url": "https://play.google.com/store/apps/details?id=connectsphere.aczh", "keywords": "social, networking"},
    {"name": "Insurance App Guide", "url": "https://play.google.com/store/apps/details?id=insurance.aplicnem", "keywords": "insurance, finance"},
    {"name": "Digital CV Share", "url": "https://play.google.com/store/apps/details?id=digital.cvshare", "keywords": "cv, career"},
    {"name": "Toolify Daily Monitor", "url": "https://play.google.com/store/apps/details?id=toolify.dailytoolsusagemonitor", "keywords": "monitor, productivity"},
    {"name": "DHO Productivity", "url": "https://play.google.com/store/apps/details?id=app3514831.dho", "keywords": "task, management"},
    {"name": "ASD 26", "url": "https://play.google.com/store/apps/details?id=com.eslamegyp.asd26", "keywords": "utility, digital"}
]

def get_next_app():
    """اختيار التطبيق التالي لضمان عدم التكرار كل ساعة"""
    history_file = "app_pointer.json"
    last_idx = -1
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            last_idx = json.load(f).get("last_index", -1)
    
    next_idx = (last_idx + 1) % len(APPS)
    with open(history_file, 'w') as f:
        json.dump({"last_index": next_idx}, f)
    return APPS[next_idx]

def get_ai_content(app):
    """توليد بوست تسويقي وسكريبت فيديو بذكاء"""
    prompt = f"Create a viral FB post and a 12-second dramatic video script for the app: {app['name']}. Return ONLY JSON: {{\"post\": \"...\", \"script\": \"...\"}}"
    res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
    clean = re.search(r'\{.*\}', res.choices[0].message.content, re.DOTALL).group()
    return json.loads(clean)

def build_video(app_name, script):
    """صناعة الفيديو (مشهدين سريعين لتجنب التعليق)"""
    headers = {"Authorization": PEXELS_API_KEY}
    v_url = requests.get(f"https://api.pexels.com/videos/search?query=tech&per_page=1", headers=headers).json()['videos'][0]['video_files'][0]['link']
    
    with open("raw.mp4", "wb") as f: f.write(requests.get(v_url).content)
    
    tts = gTTS(text=script, lang='en')
    tts.save("audio.mp3")
    audio = AudioFileClip("audio.mp3")

    # مونتاج سريع (Vertical 9:16)
    clip = VideoFileClip("raw.mp4").subclip(0, audio.duration).resize(height=1920).crop(x_center=540, width=1080)
    txt = TextClip(app_name.upper(), fontsize=70, color='yellow', font='Arial-Bold', bg_color='black', size=(900, 200)).set_position('center').set_duration(audio.duration)
    
    final = CompositeVideoClip([clip, txt]).set_audio(audio)
    final.write_videofile("promo.mp4", fps=24, codec="libx264", audio_codec="aac", threads=2)
    return "promo.mp4"

def post_to_facebook(video_path, message):
    """رفع الفيديو النهائي لفيسبوك"""
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/videos"
    with open(video_path, 'rb') as f:
        payload = {'description': message, 'access_token': FB_PAGE_ACCESS_TOKEN}
        return requests.post(url, data=payload, files={'source': f}).json()

if __name__ == "__main__":
    current_app = get_next_app()
    ai_data = get_ai_content(current_app)
    
    final_post = f"{ai_data['post']}\n\n🔥 Get it here: {current_app['url']}"
    video_file = build_video(current_app['name'], ai_data['script'])
    
    response = post_to_facebook(video_file, final_post)
    print(f"Done! App: {current_app['name']}, FB_ID: {response.get('id')}")
