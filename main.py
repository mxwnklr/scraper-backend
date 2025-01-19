from fastapi import FastAPI, Form, Request
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request  # ✅ Fix for token refresh

import os
import json

from script_google import get_google_reviews
from script_trustpilot import run_trustpilot_scraper

app = FastAPI()

# ✅ Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Load Google Client Secret JSON from Secret Files
SECRET_FILE_PATH = "/etc/secrets/GOOGLE_CLIENT_SECRET_JSON"
OAUTH_TOKEN_FILE = "/etc/secrets/OAUTH_TOKENS_JSON"  # ✅ Updated for Render Secrets;

if os.path.exists(SECRET_FILE_PATH):
    with open(SECRET_FILE_PATH, "r") as f:
        CLIENT_SECRET_FILE = json.load(f)  # ✅ Load JSON from file
else:
    raise ValueError("❌ GOOGLE_CLIENT_SECRET_JSON is missing from secret files!")

# ✅ Ensure OAuth Token File Exists
if not os.path.exists(OAUTH_TOKEN_FILE):
    with open(OAUTH_TOKEN_FILE, "w") as f:
        json.dump({}, f)  # ✅ Initialize with empty JSON

# ✅ OAuth Configuration
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
REDIRECT_URI = "https://trustpilot-scraper.vercel.app/oauth/callback"


### ✅ **OAuth Helper Functions** ###
def save_oauth_token(creds):
    """Save OAuth token and refresh token to a file"""
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }
    with open(OAUTH_TOKEN_FILE, "w") as f:
        json.dump(token_data, f)


def load_oauth_token():
    """Load OAuth token from a file"""
    if os.path.exists(OAUTH_TOKEN_FILE):
        with open(OAUTH_TOKEN_FILE, "r") as f:
            return json.load(f)
    return None  # No token found


def get_google_oauth_flow():
    """Create OAuth Flow"""
    return Flow.from_client_config(
        CLIENT_SECRET_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI
    )


### ✅ **OAuth Endpoints** ###
@app.get("/google-login")
def login():
    """Redirects user to Google OAuth for authentication."""
    flow = get_google_oauth_flow()
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")  # ✅ Request offline access
    return RedirectResponse(auth_url)


@app.get("/oauth/callback")
async def oauth_callback(request: Request):
    """Handles OAuth callback and stores user credentials."""
    flow = get_google_oauth_flow()

    try:
        # ✅ Extract full URL for correct token fetch
        flow.fetch_token(authorization_response=str(request.url))
        creds = flow.credentials
        save_oauth_token(creds)  # ✅ Save OAuth Token
        return JSONResponse({"message": "✅ Authentication successful! You can now upload files to Google Drive."})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"❌ OAuth Error: {str(e)}"})


### ✅ **Google Drive Upload Endpoint** ###
@app.post("/google/upload", response_model=None)
async def upload_to_google_drive():
    """Uploads the scraped Google Reviews file to the authenticated user's Google Drive."""
    token_data = load_oauth_token()

    if not token_data:
        return JSONResponse(status_code=401, content={"error": "❌ User not authenticated. Please login first."})

    creds = Credentials.from_authorized_user_info(token_data)

    # ✅ Refresh token if expired
    if not creds.valid:
        try:
            creds.refresh(Request())  # ✅ Fix for token refresh
            save_oauth_token(creds)  # ✅ Save updated token
        except Exception as e:
            return JSONResponse(status_code=401, content={"error": f"❌ Token refresh failed: {str(e)}"})

    service = build("drive", "v3", credentials=creds)

    # ✅ Check if the file exists before uploading
    file_path = "google_reviews.xlsx"
    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"error": "❌ No file to upload."})

    file_metadata = {"name": "Google Reviews.xlsx"}
    media = MediaFileUpload(file_path, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    try:
        uploaded_file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        return JSONResponse({"message": "✅ File uploaded successfully!", "file_id": uploaded_file["id"]})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"❌ Upload failed: {str(e)}"})


### ✅ **Trustpilot Scraper Endpoint** ###
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


### ✅ **Google Reviews Scraper Endpoint** ###
@app.post("/google")
async def process_google_reviews(
    business_name: str = Form(...),
    address: str = Form(...),
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