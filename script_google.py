import os
import requests
import re
from dotenv import load_dotenv
import pandas as pd

# ✅ Load API Key from .env file
load_dotenv()
API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

# ✅ Expand Short Google Maps URL
def expand_google_maps_short_url(short_url):
    """Expands a Google Maps short URL to a full URL."""
    try:
        response = requests.get(short_url, allow_redirects=True)
        return response.url  # Returns the final redirected URL
    except requests.exceptions.RequestException:
        return None

# ✅ Extract Place ID from Full Google Maps URL
def extract_place_id(full_url):
    """Extracts the Place ID from a Google Maps URL."""
    match = re.search(r"!1s([^!]+)", full_url)
    if match:
        return match.group(1)  # Extracts place_id from URL
    return None

# ✅ Fetch Reviews from Google Places API
def get_google_reviews(place_url, min_rating=0):
    """Fetches reviews from Google Places API using a Google Maps URL."""

    # 🔍 Step 1: Check if the URL is short and expand it
    if "maps.app.goo.gl" in place_url:
        print("🔄 Expanding short URL...")
        place_url = expand_google_maps_short_url(place_url)

    if not place_url:
        print("❌ Invalid URL")
        return None

    # 🔍 Step 2: Extract Place ID
    place_id = extract_place_id(place_url)
    if not place_id:
        print("❌ Could not extract Place ID")
        return None

    # 🔍 Step 3: Call Google Places API for reviews
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,reviews&key={API_KEY}"
    
    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ API Request Failed: {response.status_code}")
        return None

    data = response.json()
    reviews = data.get("result", {}).get("reviews", [])

    if not reviews:
        print("❌ No reviews found")
        return None

    # 🔍 Step 4: Filter and Format Reviews
    filtered_reviews = [
        {
            "Reviewer": review.get("author_name"),
            "Rating": review.get("rating"),
            "Review Text": review.get("text"),
            "Review Date": review.get("relative_time_description"),
        }
        for review in reviews if review.get("rating", 0) >= min_rating
    ]

    if not filtered_reviews:
        print("❌ No reviews match the rating filter")
        return None

    # ✅ Step 5: Save to Excel
    filename = "google_reviews.xlsx"
    pd.DataFrame(filtered_reviews).to_excel(filename, index=False)
    print(f"✅ Scraped {len(filtered_reviews)} reviews into {filename}")
    return filename