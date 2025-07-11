import os
from openai import OpenAI

def clean_gpt_output(text):
    unwanted_prefixes = [
        "başlık:", "açıklama:", "title:", "description:", "hashtag:",
        "Başlık:", "Açıklama:", "Title:", "Description:", "Hashtag:"
    ]
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    cleaned = []
    for line in lines:
        for prefix in unwanted_prefixes:
            if line.lower().startswith(prefix.lower()):
                line = line[len(prefix):].strip()
        if line.lower().startswith("hashtag"):
            continue
        cleaned.append(line)
    return cleaned

class ContentGenerationAgent:
    def __init__(self, use_openai=True, openai_api_key=None):
        self.use_openai = use_openai and openai_api_key
        if self.use_openai:
            self.client = OpenAI(api_key=openai_api_key)

    def generate_content(self, topic, image_caption, aso_keywords, game_description, trends):
        keywords = ", ".join(aso_keywords[:10])
        hashtags = " ".join(trends[:10])
        if self.use_openai:
            prompt = (
                f"Bir Instagram oyun paylaşımı için kısa ve etkili başlık ve açıklama metinleri üret.\n"
                f"Oyun türü: {topic}\n"
                f"Görsel: {image_caption}\n"
                f"Anahtar Kelimeler: {keywords}\n"
                f"Oyun Açıklaması: {game_description}\n"
                f"--\n"
                f"Sadece iki satır gönder: İlk satır sadece başlık, ikinci satır sadece açıklama.\n"
                f"'Başlık:', 'Açıklama:', 'Title:', 'Description:', 'Hashtag:' gibi kelimeler ve işaretler yazma. Sadece metin döndür, başka hiçbir şey ekleme. Hashtag de yazma."
            )
            chat_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Profosyonel bu konuda uzmanlaşmış Instagram içerik üreticisisin."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            text = chat_response.choices[0].message.content.strip()
            lines = clean_gpt_output(text)
            if len(lines) >= 2:
                title, description = lines[0], ' '.join(lines[1:])
            elif len(lines) == 1:
                title, description = lines[0], ""
            else:
                title, description = "Başlık", "Açıklama"
        else:
            title = "Demo Oyun Paylaşımı"
            description = f"{game_description}\nAnahtar kelimeler: {keywords}\nHashtagler: {hashtags}"
        return {"title": title.strip(), "description": description.strip()}
