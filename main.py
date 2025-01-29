from fastapi import FastAPI, Form, Request, Query
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request as GoogleRequest
import os
import json

from script_google import get_place_id, get_reviews_apify, save_reviews_to_excel
from script_trustpilot import run_trustpilot_scraper

app = FastAPI()

# ✅ Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
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

@app.post("/google")
async def process_google_reviews(
    business_name: str = Form(...),
    address: str = Form(...)
):
    """Handles Google review scraping requests."""
    try:
        print(f"🔍 Starting Google review scrape for: {business_name}")
        
        result = save_reviews_to_excel(business_name, address)
        if "error" in result:
            return JSONResponse(
                status_code=404,
                content={"error": result["error"]}
            )

        filename = result["filename"]
        return FileResponse(filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="google_reviews.xlsx")

    except Exception as e:
        print(f"❌ Server error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"❌ Server error: {str(e)}"}
        )