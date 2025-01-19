from fastapi import FastAPI, Form, Request
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
from script_google import get_google_reviews
from script_trustpilot import run_trustpilot_scraper
import json
import tempfile

app = FastAPI()

# ✅ Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Load Google Client Secret JSON from Environment Variable
GOOGLE_CLIENT_SECRET_JSON = os.getenv("GOOGLE_CLIENT_SECRET_JSON")

if GOOGLE_CLIENT_SECRET_JSON:
    CLIENT_SECRET_FILE = json.loads(GOOGLE_CLIENT_SECRET_JSON)  # ✅ Parse JSON from env
else:
    raise ValueError("❌ GOOGLE_CLIENT_SECRET_JSON is missing from environment variables!")

# ✅ Define OAuth Scopes
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
REDIRECT_URI = "https://trustpilot-scraper.vercel.app/oauth/callback"

# ✅ Store User OAuth Tokens in Memory (For Testing)
oauth_tokens = {}

# ✅ OAuth Flow
def get_google_oauth_flow():
    return Flow.from_client_config(
        CLIENT_SECRET_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI
    )

@app.get("/google-login")
def login():
    """Redirects the user to Google OAuth for authentication."""
    flow = get_google_oauth_flow()
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    return RedirectResponse(auth_url)

@app.get("/oauth/callback")
async def oauth_callback(request: Request):
    """Handles OAuth callback and stores user credentials."""
    flow = get_google_oauth_flow()
    authorization_response = str(request.url)
    flow.fetch_token(authorization_response=authorization_response)

    creds = flow.credentials
    oauth_tokens["user"] = creds.to_json()  # ✅ Store user token in memory

    return JSONResponse({"message": "✅ Authentication successful! You can now upload files to Google Drive."})

@app.post("/google/upload")
async def upload_to_google_drive():
    """Uploads the scraped Google Reviews file to the authenticated user's Google Drive."""
    if "user" not in oauth_tokens:
        return JSONResponse(status_code=401, content={"error": "❌ User not authenticated. Please login first."})

    creds = Credentials.from_authorized_user_info(json.loads(oauth_tokens["user"]))

    service = build("drive", "v3", credentials=creds)
    
    # ✅ Check if the file exists before uploading
    file_path = "google_reviews.xlsx"
    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"error": "❌ No file to upload."})

    file_metadata = {"name": "Google Reviews.xlsx"}
    media = MediaFileUpload(file_path, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    uploaded_file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()

    return JSONResponse({"message": "✅ File uploaded successfully!", "file_id": uploaded_file["id"]})

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
    include_ratings: str = Form(""),  
    keywords: str = Form(""),  
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