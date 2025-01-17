from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from script_google import get_place_id, get_google_reviews, save_reviews_to_excel
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
    place_name: str = Form(...),
    min_rating: str = Form(None)
):
    """Processes Google Reviews request and returns an Excel file."""
    try:
        # ✅ Step 1: Get Place ID
        place_id = get_place_id(place_name)
        if not place_id:
            return {"error": "❌ No Place ID found. Try using a more precise business name."}

        # ✅ Step 2: Get Reviews
        reviews = get_google_reviews(place_id, min_rating)
        if not reviews:
            return {"error": "❌ No reviews found for this place."}

        # ✅ Step 3: Save to Excel
        excel_file = save_reviews_to_excel(reviews, place_name)
        if not excel_file:
            return {"error": "❌ No reviews found to save."}

        # ✅ Step 4: Return Excel File
        return FileResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="google_reviews.xlsx"
        )

    except Exception as e:
        return {"error": f"Something went wrong: {str(e)}"}