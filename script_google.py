import os
import pandas as pd
import requests
from serpapi import GoogleSearch

# ✅ Load API keys
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

def get_unique_filename(base_name):
    """Generate a unique filename by appending a number if the file exists."""
    if not os.path.exists(base_name):
        return base_name
    
    base, ext = os.path.splitext(base_name)
    counter = 1
    while os.path.exists(f"{base} ({counter}){ext}"):
        counter += 1
    return f"{base} ({counter}){ext}"

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
    """Fetch **ALL** Google reviews using SerpAPI pagination."""
    
    # ✅ Get Place ID from business name
    params = {
        "engine": "google_maps",
        "q": business_name,
        "api_key": SERPAPI_KEY,
        "type": "search"
    }

    print(f"🔍 Searching for place: {business_name}")
    search = GoogleSearch(params)
    results = search.get_dict()
    
    if "error" in results:
        print(f"❌ SerpAPI Error: {results['error']}")
        return None

    places = results.get("places", [])
    if not places:
        print("❌ No place found.")
        return None
    
    place_id = places[0]["place_id"]
    print(f"✅ Found Place ID: {place_id}")

    # ✅ Fetch ALL Reviews using Pagination
    all_reviews = []
    next_page_token = None

    while True:
        review_params = {
            "engine": "google_maps_reviews",
            "place_id": place_id,
            "api_key": SERPAPI_KEY,
            "hl": "en",
            "sort_by": "newest"
        }

        if next_page_token:
            review_params["next_page_token"] = next_page_token  # ✅ Use pagination

        review_search = GoogleSearch(review_params)
        review_results = review_search.get_dict()

        if "error" in review_results:
            print(f"❌ Google API Error: {review_results['error']}")
            break

        reviews = review_results.get("reviews", [])
        if not reviews:
            print("❌ No more reviews found.")
            break

        # ✅ Extract reviews and apply min_rating filter
        for r in reviews:
            if r["rating"] >= int(min_rating):
                all_reviews.append({
                    "Reviewer": r["user"]["name"],
                    "Rating": r["rating"],
                    "Review": r.get("snippet", "No review text"),
                    "Date": r.get("date", "Unknown"),
                    "Profile": r["user"]["link"],
                    "Review Link": r["link"]
                })

        # ✅ Check if there's a next page
        next_page_token = review_results.get("serpapi_pagination", {}).get("next_page_token")
        if not next_page_token:
            print("✅ Scraped all available reviews!")
            break

    if not all_reviews:
        print("❌ No reviews matching min rating.")
        return None

    # ✅ Save reviews to an Excel file (Ensuring unique filename)
    filename = get_unique_filename("google_reviews.xlsx")
    df = pd.DataFrame(all_reviews)
    df.to_excel(filename, index=False)
    
    print(f"✅ Successfully saved {len(all_reviews)} reviews to {filename}")
    return filename