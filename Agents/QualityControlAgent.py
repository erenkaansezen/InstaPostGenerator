import re
import io
from PIL import Image, UnidentifiedImageError

class QualityControlAgent:
    def check_image_quality(self, image_bytes):
        try:
            img = Image.open(io.BytesIO(image_bytes))
            if img.width < 500 or img.height < 500:
                return False, "Görselin çözünürlüğü düşük."
            if img.format.lower() not in ['jpeg', 'jpg', 'png']:
                return False, "Görselin formatı desteklenmiyor."
            return True, "Görsel kalitesi yeterli."
        except UnidentifiedImageError:
            return False, "Görsel okunamadı."
        except Exception as e:
            return False, f"Görsel analizi sırasında hata: {e}"

    def check_text_quality(self, text):
        if not text or len(text.strip()) == 0:
            return False, "Açıklama boş."
        if len(text) < 20:
            return False, "Açıklama çok kısa."
        if len(text) > 600:
            return False, "Açıklama çok uzun."
        only_emoji = all(ord(char) > 10000 for char in text if not char.isspace())
        if only_emoji:
            return False, "Açıklama sadece emoji içeriyor."
        only_hashtag = all(x.startswith("#") for x in text.split() if x.strip())
        if only_hashtag:
            return False, "Açıklama sadece hashtaglerden oluşuyor."
        words = re.findall(r'\w+', text.lower())
        unique_words = set(words)
        if len(words) > 0 and (len(unique_words) / len(words)) < 0.5:
            return False, "Açıklama çok fazla tekrar eden kelime içeriyor (spam gibi)."
        if re.search(r'(.)\1{4,}', text):
            return False, "Açıklamada çok fazla tekrar eden harf var."
        if not any(c in text for c in ".!?"):
            return False, "Açıklama cümle sonu noktalama işareti içermiyor."
        if text[0].islower():
            return False, "Açıklamanın ilk harfi büyük olmalı."
        if not re.search(r'[çğıöşüÇĞİÖŞÜ]', text):
            return False, "Açıklama Türkçe karakter içermiyor olabilir."
        return True, "Açıklama uygun."

    def check_keywords_quality(self, keywords):
        if not keywords or len(keywords) == 0:
            return False, "Anahtar kelime listesi boş."
        if any(len(k) < 2 for k in keywords):
            return False, "Çok kısa anahtar kelimeler var."
        if len(set(keywords)) < len(keywords) * 0.5:
            return False, "Anahtar kelimeler çok fazla tekrar ediyor."
        if any(re.search(r"\s", k) for k in keywords):
            return True, "Anahtar kelimelerde birden fazla kelime var, kabul edildi."  
        return True, "Anahtar kelimeler uygun."
