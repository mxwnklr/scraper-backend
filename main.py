from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from script_trustpilot import run_trustpilot_scraper
from script_google import get_google_review_urls, extract_google_reviews

app = FastAPI()

# ✅ Allow CORS for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with your frontend URL if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ TRUSTPILOT SCRAPER ENDPOINT
@app.post("/trustpilot")
async def process_trustpilot(
    company_url: str = Form(...),
    keywords: str = Form(...),
    include_ratings: str = Form(...)
):
    """Processes the Trustpilot scraping request and returns an Excel file."""
    try:
        output_file = run_trustpilot_scraper(company_url, keywords, include_ratings)

        if output_file is None or not os.path.exists(output_file):
            return JSONResponse(content={"error": "❌ No matching reviews found. Try different keywords or ratings."}, status_code=404)

        return FileResponse(
            output_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="trustpilot_reviews.xlsx"
        )
    
    except Exception as e:
        return JSONResponse(content={"error": f"❌ Something went wrong: {str(e)}"}, status_code=500)


# ✅ GOOGLE REVIEWS SCRAPER ENDPOINT
@app.post("/google")
async def process_google(
    business_name: str = Form(...),
    location: str = Form(...)
):
    """Processes the Google Reviews scraping request and returns an Excel file."""
    try:
        # Step 1: Get Google Maps review URLs
        urls = get_google_review_urls(business_name, location)
        if not urls:
            return JSONResponse(content={"error": "❌ Could not find any Google review pages. Try a different search."}, status_code=404)

        # Step 2: Extract reviews from those URLs
        output_file = extract_google_reviews(urls)

        if output_file is None or not os.path.exists(output_file):
            return JSONResponse(content={"error": "❌ No matching reviews found for this business."}, status_code=404)

        return FileResponse(
            output_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="google_reviews.xlsx"
        )
    
    except Exception as e:
        return JSONResponse(content={"error": f"❌ Something went wrong: {str(e)}"}, status_code=500)