from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from script_runner import run_script
import os

app = FastAPI()

# ✅ Enable CORS (Allow Frontend to Access Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⬅️ Change "*" to restrict specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Review Scraper API is running 🚀"}

@app.post("/process/")
async def process_script(
    platform: str = Form(...),
    company_url: str = Form(...),
    keywords: str = Form(...),
    include_ratings: str = Form(...)
):
    """
    Process the scraping request and return the Excel file.
    """
    try:
        output_file = run_script(platform, company_url, keywords, include_ratings)
        
        if os.path.exists(output_file):
            return FileResponse(
                output_file,
                filename=output_file,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            return {"error": "Failed to generate file"}

    except Exception as e:
        return {"error": str(e)}