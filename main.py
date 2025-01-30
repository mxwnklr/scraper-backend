from fastapi import FastAPI, Form, Request, Query
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import router as openai_router
import os
import json
import pandas as pd

from script_google import get_google_reviews, get_place_id, get_reviews_apify
from script_trustpilot import run_trustpilot_scraper

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Include OpenAI router
app.include_router(openai_router)

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

@app.post("/google")
async def process_google_reviews(
    business_name: str = Form(...),
    address: str = Form(...)
):
    """Handles Google review scraping requests."""
    try:
        print(f"🔍 Starting Google review scrape for: {business_name}")
        
        filename = get_google_reviews(business_name, address)
        if not filename or not os.path.exists(filename):
            return JSONResponse(
                status_code=404,
                content={"error": "No reviews found."}
            )

        print(f"✅ Successfully scraped reviews: {filename}")
        return FileResponse(filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="google_reviews.xlsx")

    except Exception as e:
        print(f"❌ Server error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"❌ Server error: {str(e)}"}
        )