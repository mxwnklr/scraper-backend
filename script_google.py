import os
import requests
import pandas as pd

# ✅ Load API credentials from environment variables
DATAFORSEO_USERNAME = os.getenv("DATAFORSEO_USERNAME")
DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")

def get_place_id(business_name):
    """Retrieve Place ID using DataForSEO (No Language or Location Restrictions)."""
    url = "https://api.dataforseo.com/v3/business_data/google/my_business_info/live"
    
    # ✅ Authentication
    auth = (DATAFORSEO_USERNAME, DATAFORSEO_PASSWORD)
    
    # ✅ Request Payload (No location/language filter)
    payload = {
        "data": [{"business_name": business_name}]  # Removes language_code
    }
    
    response = requests.post(url, auth=auth, json=payload)
    
    if response.status_code != 200:
        print(f"❌ DataForSEO Error: {response.text}")
        return None

    result = response.json()
    
    try:
        place_id = result["tasks"][0]["result"][0]["place_id"]
        print(f"✅ Found Place ID: {place_id}")
        return place_id
    except (KeyError, IndexError):
        print("❌ No place found.")
        return None

def get_google_reviews(business_name, include_ratings="", keywords=""):
    """Retrieve ALL Google reviews using DataForSEO (No Language Filter)."""
    print(f"🔍 Searching for place: {business_name}")
    
    # ✅ Step 1: Convert Business Name → Place ID
    place_id = get_place_id(business_name)
    if not place_id:
        return None

    url = "https://api.dataforseo.com/v3/business_data/google/reviews/live"
    auth = (DATAFORSEO_USERNAME, DATAFORSEO_PASSWORD)

    # ✅ Step 2: Fetch Reviews Using Place ID (No language filter)
    payload = {
        "data": [{"place_id": place_id}]  # No "language_code" (fetches ALL available languages)
    }
    
    response = requests.post(url, auth=auth, json=payload)
    
    if response.status_code != 200:
        print(f"❌ DataForSEO API Error: {response.text}")
        return None

    result = response.json()
    
    try:
        reviews = result["tasks"][0]["result"][0]["reviews"]
        print(f"✅ Retrieved {len(reviews)} reviews")
    except (KeyError, IndexError):
        print("❌ No reviews found.")
        return None

    # ✅ Step 3: Filter by Ratings & Keywords (Optional)
    filtered_reviews = []
    for review in reviews:
        rating = review["rating"]
        comment = review["text"]

        # ⭐ Rating Filter (if specified)
        if include_ratings:
            allowed_ratings = [int(r.strip()) for r in include_ratings.split(",")]
            if rating not in allowed_ratings:
                continue
        
        # 🔍 Keyword Filter (if specified)
        if keywords:
            keyword_list = keywords.lower().split(",")
            if not any(k.strip() in comment.lower() for k in keyword_list):
                continue

        filtered_reviews.append({
            "Review": comment,
            "Rating": rating,
            "Keyword": ", ".join([k for k in keyword_list if k in comment.lower()]) if keywords else "N/A",
            "Date": review["date"],
            "Link": review.get("review_url", "No link available")
        })

    if not filtered_reviews:
        return None

    # ✅ Step 4: Save Reviews to Excel
    filename = "google_reviews.xlsx"
    df = pd.DataFrame(filtered_reviews)
    df.to_excel(filename, index=False)
    
    print(f"✅ Successfully saved {len(filtered_reviews)} reviews to {filename}")
    return filename