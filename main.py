from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from script_google import get_google_reviews
from script_trustpilot import run_trustpilot_scraper
import time
import json

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
    keywords: str = Form(""),  # Optional
    include_ratings: str = Form("")  # Optional
):
    """Processes Trustpilot scraping."""
    try:
        output_file = run_trustpilot_scraper(company_url, keywords, include_ratings)

        if output_file is None or not os.path.exists(output_file):
            return JSONResponse(
                status_code=404,
                content={"error": "❌ No matching reviews found. Try different keywords or ratings."}
            )

        return FileResponse(
            output_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="trustpilot_reviews.xlsx"
        )
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"❌ Something went wrong: {str(e)}"}
        )

@app.post("/google")
async def process_google_reviews(
    business_name: str = Form(...),
    include_ratings: str = Form(""),  # Default empty
    keywords: str = Form(""),  # Default empty
):
    """Handles Google review scraping requests with optional rating & keyword filters."""
    try:
        print(f"🔍 Searching for place: {business_name} with filters (if any)")
        
        output_file = get_google_reviews(business_name, include_ratings, keywords)

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
    
@app.post("/google")
async def scrape_google_reviews(searchData: dict):
    def event_stream():
        yield "data: Scraping started...\n\n"

        # Simulating scraping process
        for i in range(1, 101, 20):  # Fake progress updates
            time.sleep(5)
            yield f"data: {i}% done...\n\n"

        yield "data: ✅ Scraping complete! Preparing file...\n\n"
        time.sleep(3)
        yield "data: DONE\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")