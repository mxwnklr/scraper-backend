from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
from script_runner import run_script

app = FastAPI()

# ✅ Allow CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://trustpilot-scraper.vercel.app"],  # ✅ Ensure frontend is allowed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, JSONResponse
from script_runner import run_script

app = FastAPI()

@app.post("/process/")
async def process_script(
    company_url: str = Form(...),
    keywords: str = Form(...),
    include_ratings: str = Form(...)
):
    output_file = run_script(company_url, keywords, include_ratings)

    if not output_file:
        return JSONResponse(
            status_code=404,
            content={"error": "No matching reviews found. Try different keywords or ratings."}
        )

    return FileResponse(
        output_file,
        filename="scraped_reviews.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )