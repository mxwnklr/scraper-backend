import requests
import os
import pandas as pd
import time

# ✅ Load API Keys
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
DATAFORSEO_USERNAME = os.getenv("DATAFORSEO_USERNAME")
DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")

# ✅ Get Google Place ID
def get_place_id(business_name):
    """Fetches Place ID from Google Places API based on business name."""
    print(f"🔍 Searching Google Places API for: {business_name}")

    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": business_name,
        "inputtype": "textquery",
        "fields": "place_id,formatted_address",
        "key": GOOGLE_PLACES_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()
    print(f"🔎 Google Places Response: {data}")  # Debugging

    if data.get("status") == "OK" and data.get("candidates"):
        place_id = data["candidates"][0]["place_id"]
        address = data["candidates"][0]["formatted_address"]
        print(f"✅ Found Place ID: {place_id} for {business_name} ({address})")
        return place_id
    else:
        print("❌ Error extracting Place ID: No result found in API response.")
        return None

# ✅ Submit Review Task to DataForSEO
def submit_review_task(place_id, include_ratings, keywords, page_token=None):
    """Submits a request to DataForSEO to fetch Google reviews asynchronously."""
    print(f"📡 Submitting task for Place ID: {place_id} to DataForSEO")

    url = "https://api.dataforseo.com/v3/business_data/google/reviews/task_post"
    auth = (DATAFORSEO_USERNAME, DATAFORSEO_PASSWORD)

    # ✅ Handle filtering properly
    filters = []
    if include_ratings and include_ratings.strip():  # ✅ Only add if not empty
        filters.append({"rating": include_ratings.split(",")})
    if keywords and keywords.strip():  # ✅ Only add if not empty
        filters.append({"text": keywords.split(",")})

    payload = [{
        "se": "google",
        "se_type": "reviews",
        "place_id": place_id,
        "reviews_limit": 2000,  # Fetch up to 2000 reviews
        "filters": filters,  # ✅ Filters only applied if not empty
        "language_code": "de",
        "location_name": "Germany",
        "device": "desktop",
        "os": "windows"
    }]

    if page_token:
        payload[0]["page_token"] = page_token  # ✅ Request next page if available

    headers = {"Content-Type": "application/json"}
    response = requests.post(url, auth=auth, json=payload, headers=headers)
    data = response.json()

    print(f"📡 DataForSEO Task Response: {data}")  # Debugging

    if "tasks" not in data or not data["tasks"]:
        print("❌ DataForSEO API returned an empty response.")
        return None

    task = data["tasks"][0]
    if task.get("status_code") != 20100:  # ✅ 20100 means "Task Created"
        print(f"❌ DataForSEO Error: {task.get('status_message')}")
        return None

    task_id = task["id"]
    print(f"✅ Task Created: {task_id}")
    return task_id

# ✅ Fetch Completed Task Results with Pagination
def fetch_review_results(task_id):
    """Fetches completed review results from DataForSEO, handling pagination properly."""
    print(f"⏳ Waiting for DataForSEO to process task: {task_id}")

    url = f"https://api.dataforseo.com/v3/business_data/google/reviews/task_get/{task_id}"
    auth = (DATAFORSEO_USERNAME, DATAFORSEO_PASSWORD)

    reviews = []
    next_page_token = None  # ✅ Start with None, but update dynamically

    while True:  # ✅ Loop indefinitely until all pages are scraped
        time.sleep(5)  # ✅ Delay between API calls

        response = requests.get(url, auth=auth)
        data = response.json()
        print(f"📡 DataForSEO Task Result: {data}")  # Debugging

        if "tasks" not in data or not data["tasks"]:
            print("❌ No valid tasks found.")
            return None

        task = data["tasks"][0]
        if task.get("status_code") == 20000 and task.get("result"):
            result = task["result"][0]
            reviews.extend(result.get("items", []))  # ✅ Append reviews

            print(f"✅ Scraped {len(reviews)} reviews so far...")

            next_page_token = result.get("next_page_token")  # ✅ Update token for next page

            if not next_page_token:  # ✅ Stop when there are no more pages
                break

            print(f"🔄 Fetching next page of reviews (Token: {next_page_token})")
            task_id = submit_review_task(result["place_id"], "", "", next_page_token)  # ✅ Fetch next page
            if not task_id:
                break  # ✅ Stop if no new task was created

        else:
            print(f"⏳ Task not ready yet, retrying...")
            time.sleep(3)  # ✅ Add small delay before retrying

    if not reviews:
        print("❌ Task timed out. No reviews found.")
        return None

    return reviews

# ✅ Get Google Reviews (Handles Pagination)
def get_google_reviews(business_name, include_ratings="", keywords=""):
    """Fetches Google Reviews from DataForSEO asynchronously, handling pagination."""

    # ✅ Step 1: Get Place ID
    place_id = get_place_id(business_name)
    if not place_id:
        print("❌ No valid Place ID found.")
        return None  # Stop execution if no Place ID found

    # ✅ Step 2: Submit Task
    task_id = submit_review_task(place_id, include_ratings, keywords)
    if not task_id:
        return None  # Stop if task submission failed

    # ✅ Step 3: Fetch Task Results (All Pages)
    reviews = fetch_review_results(task_id)
    if not reviews:
        print("❌ No reviews found.")
        return None

    # ✅ Save reviews to Excel
    filename = "google_reviews.xlsx"
    df = pd.DataFrame(reviews)
    df.to_excel(filename, index=False)
    
    print(f"✅ Successfully saved {len(reviews)} reviews to {filename}")
    return filename