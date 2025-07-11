from PIL import Image, UnidentifiedImageError
import io

class ContentUnderstandingAgent:
    def analyze_media(self, media_bytes, file_ext):
        ext = file_ext.lower()
        if ext in ['.jpg', '.jpeg', '.png']:
            try:
                img = Image.open(io.BytesIO(media_bytes))
                return f"{img.width}x{img.height} boyutunda oyun ekran görüntüsü"
            except UnidentifiedImageError:
                return "Görsel açılamadı"
        else:
            return "Desteklenmeyen medya türü"

    def summarize_text(self, text):
        return text[:300]
