from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware  # ✅ Import CORS Middleware
from fastapi.responses import FileResponse
import os
from script_runner import run_script

app = FastAPI()

# ✅ Enable CORS for frontend (Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ Allow frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    output_file = run_script(platform, company_url, keywords, include_ratings)

    if output_file and os.path.exists(output_file):
        return FileResponse(
            output_file,
            filename=output_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        return {"error": "No reviews found or failed to generate file. Please check your input."}