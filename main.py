from fastapi import FastAPI, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from script_trustpilot import run_trustpilot_scraper
from script_google import scrape_google_reviews

# ✅ Load environment variables
load_dotenv()

app = FastAPI()

# ✅ CORS Middleware (Allow frontend to access API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend URL if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Trustpilot Scraper Endpoint
@app.post("/trustpilot/")
async def process_trustpilot(
    company_url: str = Form(...),
    keywords: str = Form(...),
    include_ratings: str = Form(...)
):
    output_file = run_trustpilot_scraper(company_url, keywords, include_ratings)

    if output_file is None or not os.path.exists(output_file):
        return {"error": "❌ No matching reviews found on Trustpilot."}

    return FileResponse(
        output_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="trustpilot_reviews.xlsx"
    )

# ✅ Google Reviews Scraper Endpoint
@app.post("/google")
async def process_google_reviews(
    business_name: str = Form(...),
    location: str = Form(...),
    min_rating: str = Form(...)
):
    """Processes Google Reviews request and returns an Excel file."""
    try:
        output_file = scrape_google_reviews(business_name, location, min_rating)

        if output_file is None or not os.path.exists(output_file):
            return {"error": "No matching Google reviews found. Try another business or location."}

        return FileResponse(
            output_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="google_reviews.xlsx"
        )

    except Exception as e:
        return {"error": f"Something went wrong: {str(e)}"}