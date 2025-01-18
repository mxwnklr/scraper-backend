import os
import pandas as pd
import googlemaps
from serpapi import GoogleSearch

# ✅ Load API keys from environment variables
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")

# ✅ Initialize Google Maps Client
gmaps = googlemaps.Client(key=GOOGLE_PLACES_API_KEY)

def get_place_id(business_name):
    """Finds the Google Place ID using Google Places API."""
    
    try:
        print(f"🔍 Searching for place: {business_name} using Google Places API...")

        response = gmaps.places(query=business_name)

        if not response.get("results"):
            print("❌ No place found.")
            return None

        place_id = response["results"][0]["place_id"]
        print(f"✅ Found Place ID: {place_id}")
        return place_id

    except Exception as e:
        print(f"❌ Error retrieving Place ID: {e}")
        return None

def get_google_reviews(business_name):
    """Fetch ALL Google reviews using SerpAPI pagination."""
    
    place_id = get_place_id(business_name)
    if not place_id:
        return None  # 🚨 Exit early if no place found

    all_reviews = []
    next_page_token = None

    while True:
        params = {
            "engine": "google_maps_reviews",
            "place_id": place_id,
            "api_key": SERPAPI_KEY,
            "hl": "en",
            "sort_by": "newest"
        }

        if next_page_token:
            params["next_page_token"] = next_page_token

        search = GoogleSearch(params)
        results = search.get_dict()

        if "error" in results:
            print(f"❌ Google API Error: {results['error']}")
            break

        reviews = results.get("reviews", [])
        if not reviews:
            print("❌ No more reviews found.")
            break

        for r in reviews:
            all_reviews.append({
                "Reviewer": r["user"]["name"],
                "Rating": r["rating"],
                "Review": r.get("snippet", "No review text"),
                "Date": r.get("date", "Unknown"),
                "Profile": r["user"]["link"],
                "Review Link": r["link"]
            })

        next_page_token = results.get("serpapi_pagination", {}).get("next_page_token")
        if not next_page_token:
            print("✅ Scraped all available reviews!")
            break

    if not all_reviews:
        print("❌ No reviews found.")
        return None

    filename = "google_reviews.xlsx"
    df = pd.DataFrame(all_reviews)
    df.to_excel(filename, index=False)

    print(f"✅ Successfully saved {len(all_reviews)} reviews to {filename}")
    return filename