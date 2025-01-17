import os
import pandas as pd
import requests
import time  # Required to handle API rate limits

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


# ✅ Function to Get ALL Reviews (with Pagination)
def get_google_reviews(place_id, min_rating):
    all_reviews = []
    next_page_token = None
    url = f"https://maps.googleapis.com/maps/api/place/details/json"

    while True:
        params = {
            "place_id": place_id,
            "fields": "review",
            "key": GOOGLE_PLACES_API_KEY,
        }
        if next_page_token:
            params["pagetoken"] = next_page_token  # Fetch next page

        response = requests.get(url, params=params)
        data = response.json()

        if "result" not in data or "reviews" not in data["result"]:
            break  # No more reviews available

        for review in data["result"]["reviews"]:
            rating = review.get("rating", 0)
            if min_rating and rating < int(min_rating):
                continue  # Skip reviews below the min rating

            all_reviews.append({
                "Reviewer": review.get("author_name", "Unknown"),
                "Rating": rating,
                "Review Date": review.get("relative_time_description", ""),
                "Review Text": review.get("text", ""),
            })

        # Check for pagination
        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break  # No more pages, stop fetching

        print("⏳ Fetching more reviews (Next Page)...")
        time.sleep(2)  # Google API requires a delay before using the next token

    return all_reviews if all_reviews else None


# ✅ Function to Convert Reviews to Excel
def save_reviews_to_excel(reviews, business_name):
    if not reviews:
        return None  # No reviews to save

    df = pd.DataFrame(reviews)
    filename = f"{business_name}_reviews.xlsx"

    df.to_excel(filename, index=False)
    return filename