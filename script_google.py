import requests
import os
import pandas as pd

# ✅ Load API Keys
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
DATAFORSEO_USERNAME = os.getenv("DATAFORSEO_USERNAME")
DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")

# ✅ Get Google Place ID
def get_place_id(business_name):
    """Fetches Place ID from Google Places API based on business name."""
    print(f"🔍 Searching Google Places API for: {business_name}")

    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": business_name,
        "inputtype": "textquery",
        "fields": "place_id,formatted_address",
        "key": GOOGLE_PLACES_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()
    print(f"🔎 Google Places Response: {data}")  # Debugging

    if data.get("status") == "OK" and data.get("candidates"):
        place_id = data["candidates"][0]["place_id"]
        address = data["candidates"][0]["formatted_address"]
        print(f"✅ Found Place ID: {place_id} for {business_name} ({address})")
        return place_id
    else:
        print("❌ Error extracting Place ID: No result found in API response.")
        return None

# ✅ Get Google Reviews from DataForSEO
def get_google_reviews(business_name, include_ratings="", keywords=""):
    """Fetches Google Reviews using DataForSEO with optional rating & keyword filtering."""

    # ✅ Step 1: Get Place ID
    place_id = get_place_id(business_name)
    if not place_id:
        print("❌ No valid Place ID found.")
        return None  # Stop execution if no Place ID found

    print(f"📡 Fetching reviews for Place ID: {place_id} from DataForSEO")

    # ✅ Step 2: Request DataForSEO API
    url = "https://api.dataforseo.com/v3/business_data/google/reviews/task_post"  # API Endpoint
    auth = (DATAFORSEO_USERNAME, DATAFORSEO_PASSWORD)

    payload = [{
        "place_id": place_id,
        "reviews_limit": 2000,
        "filters": [],
        "language_code": "de"
    }]

    # ✅ Apply Rating Filter (if provided)
    if include_ratings:
        rating_values = list(map(int, include_ratings.split(",")))  # Convert to list of ints
        payload[0]["filters"].append({"field": "rating", "operator": "in", "value": rating_values})

    # ✅ Apply Keyword Filter (if provided)
    if keywords:
        keyword_list = [k.strip().lower() for k in keywords.split(",")]
        payload[0]["filters"].append({"field": "text", "operator": "contains", "value": keyword_list})

    headers = {"Content-Type": "application/json"}
    response = requests.post(url, auth=auth, json=payload, headers=headers)
    data = response.json()

    # ✅ Handle DataForSEO Errors
    if response.status_code != 200:
        print(f"❌ DataForSEO API Request Failed: {response.status_code} {response.text}")
        return None

    print(f"📡 DataForSEO Response: {data}")  # Debugging

    # ✅ Check for Account Blockage
    if data.get("tasks"):
        task = data["tasks"][0]
        if task["status_code"] == 40201:
            print("🚨 DataForSEO Account Blocked: Contact support to resolve this issue.")
            return None

    # ✅ Check for Empty Response
    if not data.get("tasks") or not data["tasks"][0].get("result"):
        print("❌ No reviews found in DataForSEO response.")
        return None

    reviews = data["tasks"][0]["result"][0].get("items", [])

    if not reviews:
        print("❌ No reviews found.")
        return None

    # ✅ Save reviews to Excel
    filename = "google_reviews.xlsx"
    df = pd.DataFrame(reviews)
    df.to_excel(filename, index=False)
    
    print(f"✅ Successfully saved {len(reviews)} reviews to {filename}")
    return filename