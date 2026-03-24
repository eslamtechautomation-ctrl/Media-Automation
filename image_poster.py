import os
import requests
import feedparser
import time

# نفس الـ Secrets اللي استعملناها قبل كدة
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

# مدوناتك
FEEDS = [
    "https://familytvr.blogspot.com/feeds/posts/default?alt=rss",
    "https://luxuryestateguide.blogspot.com/feeds/posts/default?alt=rss"
]

def get_latest_news():
    for url in FEEDS:
        feed = feedparser.parse(url)
        if feed.entries:
            return feed.entries[0].title, feed.entries[0].link
    return None, None

def post_image_to_fb(title, news_link):
    # تحسين الـ Prompt عشان الصورة تطلع احترافية أكتر
    clean_title = title.replace("'", "").replace('"', "")
    image_prompt = f"futuristic tech style, concept art, {clean_title}"
    
    # إضافة &ext=.jpg في الآخر عشان فيسبوك يقبل الرابط
    image_url = f"https://pollinations.ai/p/{image_prompt.replace(' ', '%20')}?width=1080&height=1080&seed={int(time.time())}&nologo=true&ext=.jpg"
    
    print(f"Generated Image URL: {image_url}")
    
    fb_url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photos"
    payload = {
        'url': image_url,
        'caption': f"🔥 {title}\n\nRead more: {news_link}\n\n#TrendTech #Innovation #AI",
        'access_token': FB_PAGE_ACCESS_TOKEN
    }
    
    response = requests.post(fb_url, data=payload)
    return response.json()

if __name__ == "__main__":
    title, link = get_latest_news()
    if title:
        print(f"Generating image for: {title}")
        result = post_image_to_fb(title, link)
        print(f"Result: {result}")
