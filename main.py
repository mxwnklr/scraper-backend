from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from script_google import get_google_reviews, get_place_id
from script_trustpilot import run_trustpilot_scraper
import shutil

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
    keywords: str = Form(...),
    include_ratings: str = Form(...)
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
    min_rating: str = Form("1")  # Default rating filter is 1
):
    """Handles Google review scraping requests."""
    try:
        print(f"🔍 Searching for place: {business_name} with min rating {min_rating}")
        
        # ✅ This function already calls get_place_id internally!
        output_file = get_google_reviews(business_name, min_rating)

        if output_file is None or not os.path.exists(output_file):
            return JSONResponse(status_code=404, content={"error": "❌ No matching reviews found."})

        # ✅ Copy the file to avoid permission errors
        output_path = "google_reviews.xlsx"
        shutil.copy(output_file, output_path)

        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="google_reviews.xlsx"
        )

    except Exception as e:
        print(f"❌ Backend Error: {e}")
        return JSONResponse(status_code=500, content={"error": f"Something went wrong: {str(e)}"})