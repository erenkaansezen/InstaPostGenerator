import os
import re
import gdown
from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from Agents.TrendAnalysisAgent import TrendAnalysisAgent
from Agents.ContentUnderstandingAgent import ContentUnderstandingAgent
from Agents.ContentGenerationAgent import ContentGenerationAgent
from Agents.QualityControlAgent import QualityControlAgent
from Agents.FinalizationAgent import FinalizationAgent

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="AI Instagram İçerik Üretici", version="2.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

def download_gdrive_folder(gdrive_url, output_dir="downloads"):
    os.makedirs(output_dir, exist_ok=True)
    match = re.search(r'/folders/([a-zA-Z0-9_-]+)', gdrive_url)
    if not match:
        raise Exception("Geçersiz Google Drive klasör linki!")
    folder_id = match.group(1)
    gdown.download_folder(
        url=f"https://drive.google.com/drive/folders/{folder_id}",
        output=output_dir,
        quiet=False, use_cookies=False
    )
    return output_dir

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    with open("static/index.html", encoding="utf-8") as f:
        return f.read()

@app.post("/generate_content_from_gdrive")
async def generate_content_from_gdrive(gdrive_url: str = Form(...)):
    try:
        local_dir = download_gdrive_folder(gdrive_url)
        files = os.listdir(local_dir)
        desc_file = next((f for f in files if "desc" in f.lower()), None)
        keyw_file = next((f for f in files if "keyw" in f.lower()), None)
        media_file = next((f for f in files if f.lower().endswith((".jpg", ".jpeg", ".png"))), None)
        if not (desc_file and keyw_file and media_file):
            return JSONResponse({"ok": False, "error": "Klasörde 'description', 'keywords', 'media' dosyaları bulunamadı!"}, status_code=400)

        with open(os.path.join(local_dir, desc_file), "r", encoding="utf-8") as f:
            description = f.read()
        with open(os.path.join(local_dir, keyw_file), "r", encoding="utf-8") as f:
            keywords = f.read().replace('\n', ',').replace(';', ',')
        with open(os.path.join(local_dir, media_file), "rb") as f:
            media_bytes = f.read()
        file_ext = os.path.splitext(media_file)[1].lower()
        keywords_list = [k.strip() for k in keywords.split(",") if k.strip()][:10]

        trend_agent = TrendAnalysisAgent()
        understanding_agent = ContentUnderstandingAgent()
        generation_agent = ContentGenerationAgent(
            use_openai=bool(openai_api_key),
            openai_api_key=openai_api_key
        )
        quality_agent = QualityControlAgent()
        finalization_agent = FinalizationAgent()

        hashtags = await trend_agent.fetch_trends(
            media_bytes=media_bytes, file_ext=file_ext, topic=None, keywords=keywords_list
        )
        media_caption = understanding_agent.analyze_media(media_bytes, file_ext)
        summary = understanding_agent.summarize_text(description)

        content = generation_agent.generate_content(
            topic="",
            image_caption=media_caption,
            aso_keywords=keywords_list,
            game_description=summary,
            trends=hashtags
        )
        img_quality, img_msg = quality_agent.check_image_quality(media_bytes)
        txt_quality, txt_msg = quality_agent.check_text_quality(content["description"])
        kw_quality, kw_msg = quality_agent.check_keywords_quality(keywords_list)
        title = content["title"]
        description_out = content["description"]
        final_post = finalization_agent.finalize(title, description_out, hashtags)

        return JSONResponse({
            "ok": True,
            "hashtags": hashtags,
            "media_caption": media_caption,
            "summary": summary,
            "content": content,
            "image_quality": {"ok": img_quality, "msg": img_msg},
            "text_quality": {"ok": txt_quality, "msg": txt_msg},
            "keywords_quality": {"ok": kw_quality, "msg": kw_msg},
            "final_post": final_post
        })
    except Exception as ex:
        import traceback
        print("----- HATA TRACEBACK -----")
        print(traceback.format_exc())
        print("----- HATA SONU -----")
        return JSONResponse({"ok": False, "error": str(ex)}, status_code=400)
