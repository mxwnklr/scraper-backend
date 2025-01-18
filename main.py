from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from script_google import get_google_reviews
from script_trustpilot import run_trustpilot_scraper

app = FastAPI()

# ✅ Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/trustpilot")
async def process_trustpilot(
    company_url: str = Form(...),
    keywords: str = Form(""),  # ✅ Default empty
    include_ratings: str = Form("")  # ✅ Default empty
):
    """Processes Trustpilot scraping."""
    try:
        print(f"🔍 Scraping Trustpilot: {company_url} | Keywords: {keywords or 'ALL'} | Ratings: {include_ratings or 'ALL'}")

        output_file = run_trustpilot_scraper(company_url, keywords, include_ratings)

        if output_file is None or not os.path.exists(output_file):
            print("❌ No matching Trustpilot reviews found.")
            return JSONResponse(
                status_code=404,
                content={"error": "❌ No matching reviews found. Try different keywords or ratings."}
            )

        print(f"✅ Trustpilot Scraping Successful. Returning file: {output_file}")
        return FileResponse(
            output_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="trustpilot_reviews.xlsx"
        )
    
    except Exception as e:
        print(f"❌ Trustpilot Scraper Error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"❌ Something went wrong: {str(e)}"}
        )

### **✅ Google Reviews Scraper Endpoint (Google Places + DataForSEO)**
@app.post("/google")
async def process_google_reviews(
    business_name: str = Form(...),  # Business Name is REQUIRED
    include_ratings: str = Form(""),  # Default to empty (optional filter)
    keywords: str = Form("")  # Default to empty (optional filter)
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