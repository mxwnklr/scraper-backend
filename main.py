from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from script_google import get_google_reviews
from script_trustpilot import run_trustpilot_scraper

app = FastAPI()

# ✅ Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ TRUSTPILOT SCRAPER
@app.post("/trustpilot")
async def process_trustpilot(
    company_url: str = Form(...),
    keywords: str = Form(""),  
    include_ratings: str = Form("")
):
    """Processes Trustpilot scraping with better error handling."""
    try:
        print(f"🟡 Starting Trustpilot scrape: {company_url}, Ratings={include_ratings}, Keywords={keywords}")

        output_file = run_trustpilot_scraper(company_url, keywords, include_ratings)

        if output_file is None or not os.path.exists(output_file):
            print("❌ No matching reviews found.")
            return JSONResponse(status_code=404, content={"error": "❌ No matching reviews found."})

        print(f"✅ Successfully scraped reviews: {output_file}")
        return FileResponse(output_file, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="trustpilot_reviews.xlsx")
    
    except Exception as e:
        print(f"❌ Backend Trustpilot Error: {str(e)}")
        return JSONResponse(status_code=500, content={"error": f"❌ Internal Server Error: {str(e)}"})

# ✅ GOOGLE REVIEWS SCRAPER
@app.post("/google")
async def process_google_reviews(
    business_name: str = Form(...),
    address: str = Form(...),  # ✅ NEW: Address field
    include_ratings: str = Form(""),  # Default empty
    keywords: str = Form(""),  # Default empty
):
    """Handles Google review scraping requests with optional rating & keyword filters."""
    try:
        print(f"🔍 Searching for place: {business_name} at {address} with filters (if any)")
        
        output_file = get_google_reviews(business_name, address, include_ratings, keywords)

        if output_file is None or not os.path.exists(output_file):
            return JSONResponse(status_code=404, content={"error": "❌ No matching reviews found."})

        return FileResponse(
            output_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="google_reviews.xlsx"
        )

    except Exception as e:
        print(f"❌ Backend Error: {e}")
        return JSONResponse(status_code=500, content={"error": f"❌ Server error: {str(e)}"})