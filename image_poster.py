import os
import requests
import feedparser
import time
from PIL import Image
from io import BytesIO

FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")

FEEDS = [
    "https://familytvr.blogspot.com/feeds/posts/default?alt=rss",
    "https://luxuryestateguide.blogspot.com/feeds/posts/default?alt=rss"
]

def post_image_to_fb(title, news_link):
    clean_title = title.replace("'", "").replace('"', "")
    image_prompt = f"futuristic technology style, {clean_title}"
    image_url = f"https://pollinations.ai/p/{image_prompt.replace(' ', '%20')}?width=1080&height=1080&nologo=true"
    
    # تحميل الصورة مع User-Agent عشان نتخطى الحجب
    headers = {'User-Agent': 'Mozilla/5.0'}
    print(f"Downloading image...")
    img_res = requests.get(image_url, headers=headers)
    
    if img_res.status_code == 200:
        # التأكد إنها صورة صالحة باستخدام Pillow
        img = Image.open(BytesIO(img_res.content))
        img.save("final_image.jpg", "JPEG")
        print("Image saved successfully.")
        
        # الرفع لفيسبوك
        fb_url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photos"
        payload = {
            'caption': f"🔥 {title}\n\nRead more: {news_link}\n\n#TrendTech #Innovation",
            'access_token': FB_PAGE_ACCESS_TOKEN
        }
        
        with open('final_image.jpg', 'rb') as f:
            files = {'source': f}
            response = requests.post(fb_url, data=payload, files=files)
            return response.json()
    else:
        return {"error": "Failed to download image from source"}

if __name__ == "__main__":
    # سحب أول خبر للتجربة
    feed = feedparser.parse(FEEDS[0])
    if feed.entries:
        entry = feed.entries[0]
        print(f"Processing: {entry.title}")
        result = post_image_to_fb(entry.title, entry.link)
        print(f"Result: {result}")
