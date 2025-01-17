import os
import pandas as pd
from serpapi import GoogleSearch

# ✅ Load API key from environment variables
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")

def get_place_id(business_name):
    """Fetch the Google Place ID using SerpAPI."""
    
    params = {
        "engine": "google_maps",
        "q": business_name,
        "api_key": SERPAPI_KEY
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    if "error" in results:
        return {"error": f"SerpAPI Error: {results['error']}"}

    places = results.get("local_results", [])
    if not places:
        return None

    return places[0]["place_id"]  # ✅ Return the first Place ID found

def get_google_reviews(business_name, min_rating=1):
    """Fetch all Google reviews using SerpAPI."""
    
    # ✅ First, get the Place ID
    place_id = get_place_id(business_name)
    if not place_id:
        return None  # No Place ID found

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
        return {"error": f"SerpAPI Error: {results['error']}"}

    reviews = results.get("reviews", [])
    
    # ✅ Filter reviews by minimum rating
    filtered_reviews = [
        {
            "Reviewer": r["user"]["name"],
            "Rating": r["rating"],
            "Review": r["snippet"]
        }
        for r in reviews
        if r["rating"] >= int(min_rating)
    ]

    if not filtered_reviews:
        return None

    # ✅ Save reviews to an Excel file
    filename = "google_reviews.xlsx"
    df = pd.DataFrame(filtered_reviews)
    df.to_excel(filename, index=False)
    
    return filename