from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image, UnidentifiedImageError
import io
import requests
from bs4 import BeautifulSoup

class TrendAnalysisAgent:
    def __init__(self):
        self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        self.stopwords = {"a", "an", "the", "on", "in", "of", "and", "at", "to", "for", "with", "by", "is"}

    def _tiktok_trends_for_keyword(self, keyword):
        url = f"https://www.tiktok.com/discover/{keyword}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        try:
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code != 200:
                return []
            soup = BeautifulSoup(resp.text, "html.parser")
            hashtag_elements = soup.find_all("a", href=True)
            hashtags = []
            for a in hashtag_elements:
                href = a.get("href")
                if href and "/tag/" in href:
                    tag = href.split("/tag/")[-1].split("?")[0]
                    if tag and tag.isascii() and not tag.startswith("music"):
                        hashtags.append("#" + tag.lower())
            return list(dict.fromkeys(hashtags))[:10]
        except Exception as ex:
            return []

    def fetch_trends(self, media_bytes=None, file_ext=None, topic=None, keywords=None):
        hashtags = []
        caption_words = []
        if media_bytes and file_ext in ['.jpg', '.jpeg', '.png']:
            try:
                img = Image.open(io.BytesIO(media_bytes)).convert("RGB")
                inputs = self.processor(img, return_tensors="pt")
                out = self.model.generate(**inputs)
                caption = self.processor.decode(out[0], skip_special_tokens=True)
                caption_words = [w for w in caption.lower().split() if w not in self.stopwords]
            except Exception:
                pass
        search_terms = caption_words[:3] if caption_words else []
        if not search_terms and keywords:
            search_terms = keywords[:3]
        if not search_terms and topic:
            search_terms = [topic]
        for term in search_terms:
            if not term: continue
            tiktok_hashtags = self._tiktok_trends_for_keyword(term)
            if tiktok_hashtags:
                hashtags.extend(tiktok_hashtags)
            if len(hashtags) >= 5:
                break
        if not hashtags:
            if keywords:
                hashtags = ['#' + k.strip().replace(' ', '').lower() for k in keywords[:10] if k]
            elif topic:
                hashtags = ['#' + topic.lower()]
            else:
                hashtags = ["#tiktok", "#trending", "#viral"]
        hashtags = list(dict.fromkeys(hashtags))[:10]
        return hashtags
