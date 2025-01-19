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

# ✅ Load Google Client Secret JSON
SECRET_FILE_PATH = "/etc/secrets/GOOGLE_CLIENT_SECRET_JSON"
OAUTH_TOKEN_FILE = "/etc/secrets/OAUTH_TOKENS_JSON"

if os.path.exists(SECRET_FILE_PATH):
    with open(SECRET_FILE_PATH, "r") as f:
        CLIENT_SECRET_FILE = json.load(f)
else:
    raise ValueError("❌ GOOGLE_CLIENT_SECRET_JSON is missing from secret files!")

# ✅ Ensure OAuth Token File Exists
if not os.path.exists(OAUTH_TOKEN_FILE):
    with open(OAUTH_TOKEN_FILE, "w") as f:
        json.dump({}, f)

# ✅ OAuth Configuration
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
BASE_FRONTEND_URL = "https://trustpilot-scraper.vercel.app"

# ✅ Redirect URIs for Trustpilot & Google
REDIRECT_URIS = {
    "trustpilot": f"{BASE_FRONTEND_URL}/trustpilot/oauth/callback",
    "google": f"{BASE_FRONTEND_URL}/google/oauth/callback"
}

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
    return None

def get_google_oauth_flow(redirect_uri: str):
    """Create OAuth Flow with Dynamic Redirect URI"""
    return Flow.from_client_config(
        CLIENT_SECRET_FILE, scopes=SCOPES, redirect_uri=redirect_uri
    )

@app.get("/google-login")
def login(page: str = Query("google")):
    """Redirects user to Google OAuth for authentication."""
    
    # ✅ Determine the correct redirect URI dynamically
    redirect_uri = REDIRECT_URIS.get(page, REDIRECT_URIS["google"])

    flow = get_google_oauth_flow(redirect_uri)
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    
    return JSONResponse({"auth_url": auth_url})

@app.get("/oauth/callback", response_model=None)
async def oauth_callback(request: Request, page: str = Query("google")):
    """Handles OAuth callback, saves credentials, and closes the tab."""
    
    # ✅ Determine correct redirect URI
    redirect_uri = REDIRECT_URIS.get(page, REDIRECT_URIS["google"])
    
    flow = get_google_oauth_flow(redirect_uri)
    
    # ✅ Extract Google auth response manually
    query_params = str(request.url).split("?")[1]  # Extract query string
    flow.fetch_token(authorization_response=f"{redirect_uri}?{query_params}")

    creds = flow.credentials
    save_oauth_token(creds)  # ✅ Save OAuth Token

    # ✅ Return JavaScript to close the tab and notify the parent window
    html_content = """
    <script>
        window.opener.postMessage("oauth_success", window.origin);
        window.close();
    </script>
    """
    return HTMLResponse(content=html_content)

@app.post("/google/upload")
async def upload_to_google_drive():
    """Uploads the scraped Google Reviews file to the authenticated user's Google Drive."""
    token_data = load_oauth_token()
    
    if not token_data:
        return JSONResponse(status_code=401, content={"error": "❌ User not authenticated. Please login first."})

    creds = Credentials.from_authorized_user_info(token_data)

    # ✅ Refresh token if expired
    if not creds.valid:
        try:
            creds.refresh(GoogleRequest())
            save_oauth_token(creds)
        except Exception as e:
            return JSONResponse(status_code=401, content={"error": f"❌ Token refresh failed: {str(e)}"})

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