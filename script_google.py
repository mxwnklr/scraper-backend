import os
import pandas as pd
import requests
from serpapi import GoogleSearch

# ✅ Load API keys
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

def get_place_id(business_name):
    """Fetch Place ID from Google Places API"""
    url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    
    params = {
        "input": business_name,
        "inputtype": "textquery",
        "fields": "place_id",
        "key": GOOGLE_PLACES_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "candidates" not in data or not data["candidates"]:
        print(f"❌ No place found for '{business_name}'")
        return None
    
    place_id = data["candidates"][0]["place_id"]
    print(f"✅ Found Place ID: {place_id}")
    return place_id

def get_google_reviews(business_name, min_rating=1):
    """Fetch Google reviews using SerpAPI"""
    
    # ✅ Step 1: Get Place ID from Google Places API
    place_id = get_place_id(business_name)
    if not place_id:
        return {"error": "Could not find a matching place."}

    # ✅ Step 2: Fetch reviews using SerpAPI
    params = {
        "engine": "google_maps_reviews",
        "place_id": place_id,
        "api_key": SERPAPI_KEY,
        "hl": "en",
        "sort_by": "newest",
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    if "error" in results:
        print(f"❌ Google API Error: {results['error']}")
        return {"error": f"Google API Error: {results['error']}"}

    reviews = results.get("reviews", [])
    
    # ✅ Step 3: Filter reviews by minimum rating
    filtered_reviews = [
        {
            "Reviewer": r["user"]["name"],
            "Rating": r["rating"],
            "Review": r["snippet"],
        }
        for r in reviews if r["rating"] >= int(min_rating)
    ]

    if not filtered_reviews:
        print("❌ No reviews matched the filter criteria.")
        return None

    # ✅ Step 4: Save to Excel
    filename = "google_reviews.xlsx"
    df = pd.DataFrame(filtered_reviews)
    df.to_excel(filename, index=False)

    print(f"✅ Successfully saved {len(filtered_reviews)} reviews to {filename}")
    return filename