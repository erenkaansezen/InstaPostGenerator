from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import io
import re
import requests
from bs4 import BeautifulSoup

def extract_keywords_from_caption(caption, topn=3):
    stopwords = set([
        "a", "an", "the", "on", "in", "of", "and", "at", "to", "for", "with", "by", "is", 
        "game", "image", "photo", "picture", "video", "play", "playing", "level", "player"
    ])
    words = re.findall(r'\b\w+\b', caption.lower())
    keywords = [w for w in words if w not in stopwords and len(w) > 2]
    freq = {}
    for w in keywords:
        freq[w] = freq.get(w, 0) + 1
    keywords = sorted(freq.keys(), key=lambda x: -freq[x])
    return keywords[:topn]

def get_hashtags_from_tiktokhashtags(keyword, limit=10):
    url = f"https://tiktokhashtags.com/hashtag/{keyword}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    hashtags = []
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            results = soup.select('.tag-box .tag-item a')
            for a in results:
                txt = a.text.strip()
                if txt.startswith("#") and txt not in hashtags:
                    hashtags.append(txt)
                if len(hashtags) >= limit:
                    break
    except Exception:
        pass
    return hashtags

def get_hashtags_from_besthashtags(keyword, limit=10):
    url = f"https://best-hashtags.com/hashtag/{keyword}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    hashtags = []
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            main_tag = soup.select_one('.tag_box')
            if main_tag:
                tags = main_tag.text.split()
                for tag in tags:
                    tag = tag.strip()
                    if tag.startswith("#") and tag not in hashtags:
                        hashtags.append(tag)
                    if len(hashtags) >= limit:
                        break
    except Exception:
        pass
    return hashtags

class TrendAnalysisAgent:
    def __init__(self):
        self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

    async def fetch_trends(self, media_bytes=None, file_ext=None, topic=None, keywords=None):
        blip_keywords = []
        caption = ""
        if media_bytes and file_ext in ['.jpg', '.jpeg', '.png']:
            try:
                img = Image.open(io.BytesIO(media_bytes)).convert("RGB")
                inputs = self.processor(img, return_tensors="pt")
                out = self.model.generate(**inputs)
                caption = self.processor.decode(out[0], skip_special_tokens=True)
                blip_keywords = extract_keywords_from_caption(caption, topn=3)
            except Exception:
                pass

        # Geniş arama için ekstra kelimeler ekle
        extra_terms = ["game", "car", "play", "action", "oyun", "simulator", "polis", "police", "fun"]
        used_terms = list(dict.fromkeys((blip_keywords or []) + (keywords or []) + extra_terms))[:5]

        hashtags = []
        for term in used_terms:
            tags = get_hashtags_from_tiktokhashtags(term)
            if not tags:
                tags = get_hashtags_from_besthashtags(term)
            hashtags += tags
            if len(hashtags) >= 10:
                break
        # benzersiz ilk 10
        hashtags = list(dict.fromkeys(hashtags))[:10]
        # fallback
        if not hashtags:
            hashtags = ["#oyun", "#game", "#car", "#police", "#simulator", "#trend", "#tiktok"]
        return hashtags
