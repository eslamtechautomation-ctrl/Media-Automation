import os
import requests
import json
import random
from groq import Groq
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip

# Configuration
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

client = Groq(api_key=GROQ_API_KEY)

def get_story_script():
    # Topics for the AI to expand on
    topics = [
        "The day the internet almost died in 1988 (Morris Worm)",
        "The secret room in the Apple headquarters",
        "How a pizza delivery led to the creation of YouTube",
        "The billion-dollar mistake: Why Yahoo didn't buy Google",
        "The mystery of the first ever computer moth bug",
        "Why the QWERTY keyboard was designed to slow you down",
        "The man who sold the internet for 1 dollar",
        "How NASA's computer was hacked by a 15-year-old"
    ]
    selected_topic = random.choice(topics)
    
    prompt = f"""
    Topic: {selected_topic}
    Task: Write a 28-second viral, mysterious, and fast-paced storytelling script for a Facebook Reel.
    Structure: 
    1. Mind-blowing Hook (e.g., 'They don't want you to know this...').
    2. The 'Story' (Brief, punchy facts).
    3. Dramatic Conclusion + CTA ('Follow for more tech secrets').
    Tone: Cinematic and energetic.
    Language: English.
    Return ONLY the script text, no intro/outro.
    """
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return selected_topic, chat_completion.choices[0].message.content

def download_multi_visuals(query):
    # تحميل 4 فيديوهات مختلفة لتنويع المشاهد
    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=10"
    res = requests.get(url, headers=headers).json()
    
    video_files = []
    for i in range(4): # هناخد أول 4 فيديوهات مختلفة
        v_url = res['videos'][i]['video_files'][0]['link']
        filename = f"part_{i}.mp4"
        with open(filename, 'wb') as f:
            f.write(requests.get(v_url).content)
        video_files.append(filename)
    return video_files

def assemble_pro_reel(script, topic_title, video_parts):
    # 1. الصوت
    tts = gTTS(text=script, lang='en')
    tts.save("voice.mp3")
    audio = AudioFileClip("voice.mp3")
    
    # 2. تجميع المشاهد (تغيير المشهد كل 6-7 ثواني)
    clips = []
    for part in video_parts:
        clip = VideoFileClip(part).subclip(0, 7).resize(height=1920).crop(x_center=540, width=1080)
        clips.append(clip)
    
    main_video = concatenate_videoclips(clips).set_duration(audio.duration)
    
    # 3. إضافة العنوان بخلفية احترافية
    title_clip = TextClip(topic_title.upper(), fontsize=70, color='yellow', font='Arial-Bold', 
                          bg_color='black', method='caption', size=(900, None))
    title_clip = title_clip.set_position('center').set_duration(5).set_opacity(0.8)

    # 4. دمج الكل مع الموسيقى (لو عندك ملف music.mp3 في الـ Repo)
    final = main_video.set_audio(audio)
    final.write_videofile("final_reel.mp4", fps=24, codec="libx264")
    
def post_to_facebook(title):
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/videos"
    with open('final_story.mp4', 'rb') as f:
        payload = {
            'description': f"Tech Mystery: {title} 🕵️‍♂️💻 #TechSecrets #Innovation #TechHistory #GlobalTech",
            'access_token': FB_PAGE_ACCESS_TOKEN
        }
        files = {'source': f}
        return requests.post(url, data=payload, files=files).json()

if __name__ == "__main__":
    print("🎬 Starting Story Engine...")
    topic, script = get_story_script()
    print(f"📖 Topic: {topic}")
    
    print("🎥 Downloading cinematic background...")
    download_visuals()
    
    print("✂️ Editing Video...")
    assemble_reel(script, topic)
    
    print("🚀 Uploading to Facebook...")
    result = post_to_facebook(topic)
    
    if "id" in result:
        print(f"✅ Successfully Published! Video ID: {result['id']}")
    else:
        print(f"❌ Upload Failed: {result}")
