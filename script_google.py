import requests
import os
import re
import pandas as pd
from dotenv import load_dotenv

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ✅ Extracts Google Place ID from a long or short Google Maps URL
def get_place_id(google_maps_url):
    """Extracts the Place ID from a Google Maps URL using Google Places API."""
    try:
        # 🔄 Handle short URL by expanding it
        if "maps.app.goo.gl" in google_maps_url:
            print("🔄 Expanding short URL...")
            response = requests.get(google_maps_url, allow_redirects=True)
            google_maps_url = response.url  # Gets final redirected URL

        # ✅ Extract place ID from long Google URL (if present)
        match = re.search(r"!1s([^!]+)", google_maps_url)
        if match:
            place_id = match.group(1)
            print(f"✅ Extracted Place ID from URL: {place_id}")
            return place_id

        # 🔎 If regex fails, fallback to Google Places API Search
        print("🔎 Fetching Place ID using Google API...")
        place_name = google_maps_url.split("/place/")[-1].split("/")[0]
        search_url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={place_name}&inputtype=textquery&fields=place_id&key={GOOGLE_API_KEY}"
        
        response = requests.get(search_url)
        data = response.json()

        if "candidates" in data and data["candidates"]:
            place_id = data["candidates"][0]["place_id"]
            print(f"✅ Found Place ID: {place_id}")
            return place_id

    except Exception as e:
        print(f"❌ Error extracting Place ID: {e}")
    
    return None

# ✅ Fetch reviews using Google Place ID
def get_google_reviews(google_maps_url, min_rating=0):
    """Fetches Google reviews for a business using Place ID."""
    place_id = get_place_id(google_maps_url)
    if not place_id:
        print("❌ Could not retrieve Place ID")
        return None

    print(f"🔎 Fetching reviews for Place ID: {place_id}")

    reviews_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=reviews&key={GOOGLE_API_KEY}"
    
    response = requests.get(reviews_url)
    data = response.json()

    if "reviews" not in data["result"]:
        print("❌ No reviews found")
        return None

    all_reviews = []
    for review in data["result"]["reviews"]:
        rating = review["rating"]
        if rating >= min_rating:
            all_reviews.append({
                "Reviewer": review.get("author_name", "Unknown"),
                "Rating": rating,
                "Review Text": review.get("text", "No text"),
                "Review Date": review.get("time")
            })

    if not all_reviews:
        print("❌ No reviews matching the rating filter")
        return None

    # ✅ Save results to an Excel file
    filename = "google_reviews.xlsx"
    pd.DataFrame(all_reviews).to_excel(filename, index=False)
    print(f"✅ Scraped {len(all_reviews)} reviews into {filename}")
    return filename