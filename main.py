from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from script_runner import run_script

app = FastAPI()

# ✅ Allow CORS for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Change this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/process/")
async def process_script(
    company_url: str = Form(...),
    keywords: str = Form(...),
    include_ratings: str = Form(...)
):
    """Processes the scraping request and returns an Excel file or an error response."""
    try:
        output_file = run_script(company_url, keywords, include_ratings)

        # ✅ If no reviews are found, return a JSON error response
        if output_file is None or not os.path.exists(output_file):
            return JSONResponse(
                content={"error": "❌ No matching reviews found. Try different keywords or ratings."},
                status_code=404
            )

        # ✅ If a file was created, return it as a response
        return FileResponse(
            output_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="scraped_reviews.xlsx"
        )
    
    except Exception as e:
        return JSONResponse(
            content={"error": f"❌ Something went wrong: {str(e)}"},
            status_code=500
        )