import os
import requests
import pandas as pd

# ✅ Load API Keys
DATAFORSEO_USERNAME = os.getenv("DATAFORSEO_USERNAME")
DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ✅ Google Places API to retrieve Place ID
def get_place_id(business_name):
    url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": business_name,
        "inputtype": "textquery",
        "fields": "place_id,formatted_address",
        "key": GOOGLE_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data.get("status") == "OK" and data.get("candidates"):
        place_id = data["candidates"][0]["place_id"]
        address = data["candidates"][0]["formatted_address"]
        print(f"✅ Found Place ID: {place_id} for {business_name} ({address})")
        return place_id
    else:
        print("❌ Error extracting Place ID: No result found in API response.")
        return None

# ✅ Fetch Google Reviews using DataForSEO
def get_google_reviews(business_name, include_ratings="", keywords=""):
    place_id = get_place_id(business_name)
    if not place_id:
        return None

    # ✅ Submit Task to DataForSEO
    payload = {
        "data": [
            {
                "place_id": place_id,
                "language_code": "en"
            }
        ]
    }

    task_url = "https://api.dataforseo.com/v3/business_data/google/reviews/task_post"
    auth = (DATAFORSEO_USERNAME, DATAFORSEO_PASSWORD)

    response = requests.post(task_url, auth=auth, json=payload)
    task_response = response.json()

    if "tasks" not in task_response or not task_response["tasks"]:
        print("❌ DataForSEO Task Submission Failed.")
        return None

    task_id = task_response["tasks"][0]["id"]

    # ✅ Retrieve the Task Results
    result_url = f"https://api.dataforseo.com/v3/business_data/google/reviews/task_get/{task_id}"
    result_response = requests.get(result_url, auth=auth)
    reviews_data = result_response.json()

    if "result" not in reviews_data or not reviews_data["result"]:
        print("❌ No reviews found.")
        return None

    reviews = reviews_data["result"]

    # ✅ Filter by Rating & Keywords
    filtered_reviews = []
    for review in reviews:
        rating = review.get("rating")
        review_text = review.get("text", "")
        review_link = review.get("review_link", "")
        review_date = review.get("date", "")
        user_name = review.get("user_name", "")

        # Check Rating
        if include_ratings and str(rating) not in include_ratings.split(","):
            continue

        # Check Keywords
        if keywords:
            keyword_list = keywords.split(",")
            if not any(keyword.lower() in review_text.lower() for keyword in keyword_list):
                continue

        filtered_reviews.append({
            "Reviewer": user_name,
            "Review": review_text,
            "Rating": rating,
            "Date": review_date,
            "Review Link": review_link
        })

    # ✅ Save as Excel File
    if not filtered_reviews:
        return None

    filename = "google_reviews.xlsx"
    df = pd.DataFrame(filtered_reviews)
    df.to_excel(filename, index=False)

    return filename