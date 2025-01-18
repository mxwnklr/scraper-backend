import os
import requests
import pandas as pd

# ✅ Load API credentials from environment variables
DATAFORSEO_USERNAME = os.getenv("DATAFORSEO_USERNAME")
DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")

def get_place_id(business_name):
    """Retrieve Place ID using DataForSEO (Handles Empty Responses)."""
    url = "https://api.dataforseo.com/v3/business_data/google/my_business_info/live"
    
    # ✅ Authentication
    auth = (DATAFORSEO_USERNAME, DATAFORSEO_PASSWORD)
    
    # ✅ Request Payload
    payload = {
        "data": [{"business_name": business_name}]
    }
    
    try:
        response = requests.post(url, auth=auth, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ API Request Failed: {e}")
        return None

    result = response.json()
    print(f"🔎 DataForSEO Response: {result}")  # <-- NEW DEBUG LOG

    # ✅ Safe Extraction
    try:
        if "tasks" not in result or not result["tasks"]:
            raise ValueError("No tasks found in API response.")

        first_task = result["tasks"][0]

        if "result" not in first_task or not first_task["result"]:
            raise ValueError("No result found in API response.")

        place_info = first_task["result"][0]

        # ✅ Extract Place ID (Check if Exists)
        place_id = place_info.get("place_id")
        business_address = place_info.get("address", "Unknown Address")

        if not place_id:
            raise ValueError("Place ID is missing in response.")

        print(f"✅ Found Place ID: {place_id} for {business_name} ({business_address})")
        return place_id
    except (KeyError, IndexError, ValueError) as e:
        print(f"❌ Error extracting Place ID: {e}")
        return None

def get_google_reviews(business_name, include_ratings="", keywords=""):
    """Retrieve ALL Google reviews using DataForSEO."""
    print(f"🔍 Searching for place: {business_name}")

    # ✅ Step 1: Convert Business Name → Place ID
    place_id = get_place_id(business_name)
    if not place_id:
        print("❌ No valid Place ID found.")
        return None

    url = "https://api.dataforseo.com/v3/business_data/google/reviews/live"
    auth = (DATAFORSEO_USERNAME, DATAFORSEO_PASSWORD)

    # ✅ Step 2: Fetch Reviews Using Place ID
    payload = {
        "data": [{"place_id": place_id}]
    }
    
    try:
        response = requests.post(url, auth=auth, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ API Request Failed: {e}")
        return None

    result = response.json()

    # ✅ Safe Extraction of Reviews
    try:
        if "tasks" not in result or not result["tasks"]:
            raise ValueError("No tasks found in API response.")

        first_task = result["tasks"][0]

        if "result" not in first_task or not first_task["result"]:
            raise ValueError("No result found in API response.")

        reviews = first_task["result"][0].get("reviews", [])

        if not reviews:
            print("❌ No reviews found.")
            return None

        print(f"✅ Retrieved {len(reviews)} reviews")

    except (KeyError, IndexError, ValueError) as e:
        print(f"❌ Error extracting reviews: {e}")
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