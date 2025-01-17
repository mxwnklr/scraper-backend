import os
import requests
import pandas as pd
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

# ✅ Function to get place details
def get_place_id(business_name, location):
    """Fetches the Google Place ID using the business name & location."""
    search_query = f"{business_name} {location}"
    url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    
    params = {
        "input": search_query,
        "inputtype": "textquery",
        "fields": "place_id",
        "key": API_KEY
    }
    
    response = requests.get(url, params=params).json()
    
    if "candidates" in response and response["candidates"]:
        return response["candidates"][0]["place_id"]
    
    return None

# ✅ Function to scrape reviews
def scrape_google_reviews(business_name, location):
    """Fetches Google Reviews using Google Places API."""
    
    place_id = get_place_id(business_name, location)
    if not place_id:
        return None
    
    url = f"https://maps.googleapis.com/maps/api/place/details/json"
    
    params = {
        "place_id": place_id,
        "fields": "name,rating,reviews",
        "key": API_KEY
    }
    
    response = requests.get(url, params=params).json()
    
    if "result" not in response or "reviews" not in response["result"]:
        return None
    
    reviews = response["result"]["reviews"]
    
    # ✅ Format data
    review_data = []
    for review in reviews:
        review_data.append({
            "Reviewer": review["author_name"],
            "Rating": review["rating"],
            "Review": review["text"],
            "Date": review["time"]
        })
    
    # ✅ Save reviews to an Excel file
    filename = "google_reviews.xlsx"
    pd.DataFrame(review_data).to_excel(filename, index=False)
    
    return filename