from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from script_runner import run_script

app = FastAPI()


# ✅ Enable CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

@app.post("/process/")
async def process_script(company_url: str, keywords: str, include_ratings: str):
    """Handles API requests for scraping Trustpilot"""
    try:
        output_file = run_script(company_url, keywords, include_ratings)

        if output_file is None:
            return {"error": "No matching reviews found"}

        return {"file_url": output_file}

    except Exception as e:
        return {"error": f"Something went wrong: {str(e)}"}