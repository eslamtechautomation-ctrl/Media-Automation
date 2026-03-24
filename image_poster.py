import os
import requests
import feedparser
import time

# الإعدادات
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

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
    # 1. تجهيز رابط الصورة
    clean_title = title.replace("'", "").replace('"', "")
    image_prompt = f"futuristic technology style, {clean_title}"
    image_url = f"https://pollinations.ai/p/{image_prompt.replace(' ', '%20')}?width=1080&height=1080&nologo=true"
    
    # 2. تحميل الصورة محلياً في ملف مؤقت
    print(f"Downloading image from Pollinations...")
    img_data = requests.get(image_url).content
    with open('temp_image.jpg', 'wb') as handler:
        handler.write(img_data)

    # 3. رفع الصورة لفيسبوك كملف (Multi-part upload)
    print(f"Uploading image to Facebook...")
    fb_url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photos"
    
    payload = {
        'caption': f"🔥 {title}\n\nRead more: {news_link}\n\n#TrendTech #Innovation #Tech",
        'access_token': FB_PAGE_ACCESS_TOKEN
    }
    
    with open('temp_image.jpg', 'rb') as img_file:
        files = {'source': img_file}
        response = requests.post(fb_url, data=payload, files=files)
    
    return response.json()

if __name__ == "__main__":
    title, link = get_latest_news()
    if title:
        print(f"Processing: {title}")
        result = post_image_to_fb(title, link)
        print(f"Result: {result}")
        # مسح الملف المؤقت بعد الرفع
        if os.path.exists('temp_image.jpg'):
            os.remove('temp_image.jpg')
