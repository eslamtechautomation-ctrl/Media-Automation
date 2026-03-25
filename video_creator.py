import os, requests, json, re
from groq import Groq
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
import proglog

# كتم رسائل المونتاج المزعجة اللي بتبطأ الأكشن
proglog.default_bar_logger = lambda *args, **kwargs: None

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

client = Groq(api_key=GROQ_API_KEY)

def get_dynamic_story():
    prompt = "Write a 20-second mysterious tech story. Return ONLY JSON: {\"title\": \"...\", \"script\": \"...\"}"
    try:
        res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
        clean_json = re.search(r'\{.*\}', res.choices[0].message.content, re.DOTALL).group()
        return json.loads(clean_json)
    except:
        return {"title": "Tech Mystery", "script": "Did you know that the first computer bug was a real moth?"}

def create_video():
    data = get_dynamic_story()
    # جلب فيديوهات (مقطعين بس عشان السرعة وعدم التعليق)
    headers = {"Authorization": PEXELS_API_KEY}
    v_res = requests.get(f"https://api.pexels.com/videos/search?query=cyberpunk&per_page=2", headers=headers).json()
    
    video_paths = []
    for i, v in enumerate(v_res.get('videos', [])):
        path = f"v{i}.mp4"
        with open(path, 'wb') as f: f.write(requests.get(v['video_files'][0]['link']).content)
        video_paths.append(path)

    # توليد الصوت
    tts = gTTS(text=data['script'], lang='en')
    tts.save("s.mp3")
    audio = AudioFileClip("s.mp3")

    # المونتاج
    clips = [VideoFileClip(p).subclip(0, 5).resize(height=1920).crop(x_center=540, width=1080) for p in video_paths]
    final_v = concatenate_videoclips(clips).set_audio(audio).set_duration(audio.duration)
    
    # إضافة نص بسيط
    txt = TextClip(data['title'], fontsize=70, color='yellow', font='Arial-Bold', bg_color='black', size=(1080, 200)).set_position('center').set_duration(5)
    
    result = CompositeVideoClip([final_v, txt])
    result.write_videofile("out.mp4", fps=24, codec="libx264", audio_codec="aac", threads=2) # استخدام threads لتسريع العملية
    
    # تنظيف الملفات المؤقتة فوراً
    audio.close()
    for c in clips: c.close()
    return data['title']

# كود الرفع للفيس بوك (Post_to_fb) يوضع هنا
