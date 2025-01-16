from fastapi import FastAPI, Form
from fastapi.responses import FileResponse
from script_runner import run_script
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Review Scraper API is running 🚀"}

@app.post("/process/")
async def process_script(
    platform: str = Form(...),          # "trustpilot" or "google"
    company_url: str = Form(...),       # URL of the company reviews page
    keywords: str = Form(...),          # Keywords to filter reviews
    include_ratings: str = Form(...)    # Ratings to include (e.g., "1,2,3")
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