import os
import pandas as pd
import requests

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

# ✅ Function to Get Place ID from Business Name
def get_place_id(business_name):
    url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": business_name,
        "inputtype": "textquery",
        "fields": "place_id",
        "key": GOOGLE_PLACES_API_KEY,
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "candidates" in data and len(data["candidates"]) > 0:
        return data["candidates"][0]["place_id"]
    else:
        print("❌ No Place ID found for:", business_name)
        return None


# ✅ Function to Get Reviews from Google Places API
def get_google_reviews(place_id, min_rating):
    url = f"https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "review",
        "key": GOOGLE_PLACES_API_KEY,
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "result" not in data or "reviews" not in data["result"]:
        print("❌ No reviews found for Place ID:", place_id)
        return None

    reviews = []
    for review in data["result"]["reviews"]:
        rating = review.get("rating", 0)
        if min_rating and rating < int(min_rating):
            continue  # Skip reviews below the min rating

        reviews.append({
            "Reviewer": review.get("author_name", "Unknown"),
            "Rating": rating,
            "Review Date": review.get("relative_time_description", ""),
            "Review Text": review.get("text", ""),
        })

    return reviews if reviews else None


# ✅ Function to Convert Reviews to Excel and Return File Path
def save_reviews_to_excel(reviews, business_name):
    if not reviews:
        return None  # No reviews to save

    df = pd.DataFrame(reviews)
    filename = f"{business_name}_reviews.xlsx"

    df.to_excel(filename, index=False)
    return filename