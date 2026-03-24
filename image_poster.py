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
    # بنعمل Prompt للصورة بناءً على العنوان
    image_prompt = f"Futuristic technology, {title}, high resolution, cyberpunk style, digital art"
    # رابط توليد الصورة (مجاني وبدون مفاتيح)
    image_url = f"https://pollinations.ai/p/{image_prompt.replace(' ', '%20')}?width=1080&height=1080&seed=42&nologo=true"
    
    fb_url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photos"
    payload = {
        'url': image_url,
        'caption': f"🔥 {title}\n\nRead more: {news_link}\n\n#TrendTech #Innovation #TechNews",
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
