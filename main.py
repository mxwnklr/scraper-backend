from fastapi import FastAPI, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from script_runner import run_script

app = FastAPI()

# ✅ Allow CORS for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # ✅ Allow all HTTP methods
    allow_headers=["*"],  # ✅ Allow all headers
)

@app.post("/process/")
async def process_script(
    company_url: str = Form(...),
    keywords: str = Form(...),
    include_ratings: str = Form(...)
):
    """Processes the scraping request and returns an Excel file."""
    try:
        output_file = run_script(company_url, keywords, include_ratings)

        if output_file is None or not os.path.exists(output_file):
            return {"error": "No matching reviews found. Try different keywords or ratings."}

        return FileResponse(
            output_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="scraped_reviews.xlsx"
        )
    
    except Exception as e:
        return {"error": f"Something went wrong: {str(e)}"}