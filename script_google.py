import requests
import pandas as pd
import os
from dotenv import load_dotenv

# Load API Key from .env
load_dotenv()
API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

def get_google_reviews(place_id, min_rating=None):
    """Fetches Google Reviews using Place ID and converts to Excel."""
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=reviews&key={API_KEY}"
    response = requests.get(url)
    data = response.json()

    if "error_message" in data:
        print(f"❌ Google API Error: {data['error_message']}")
        return None

    reviews = data.get("result", {}).get("reviews", [])
    if not reviews:
        print("❌ No reviews found!")
        return None

    filtered_reviews = []
    for review in reviews:
        rating = review.get("rating", 0)
        if min_rating and rating < int(min_rating):
            continue
        filtered_reviews.append({
            "Reviewer": review.get("author_name", "Unknown"),
            "Rating": rating,
            "Review Text": review.get("text", ""),
            "Time": review.get("relative_time_description", "")
        })

    if not filtered_reviews:
        print("❌ No matching reviews after filtering!")
        return None

    # Convert to Excel
    df = pd.DataFrame(filtered_reviews)
    output_file = "google_reviews.xlsx"
    df.to_excel(output_file, index=False)
    print(f"✅ Saved {len(filtered_reviews)} reviews to {output_file}")
    return output_file