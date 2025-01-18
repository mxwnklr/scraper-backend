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
def submit_review_task(place_id):
    """Submits a request to DataForSEO to fetch Google reviews asynchronously."""
    print(f"📡 Submitting task for Place ID: {place_id} to DataForSEO")

    url = "https://api.dataforseo.com/v3/business_data/google/reviews/task_post"
    auth = (DATAFORSEO_USERNAME, DATAFORSEO_PASSWORD)

    payload = [{
        "se": "google",
        "se_type": "reviews",
        "place_id": place_id,
        "reviews_limit": 2000,  # Fetch up to 2000 reviews
        "filters": [],
        "language_code": "de",  # Ensure correct language parameter
        "device": "desktop",
        "os": "windows"
    }]

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

# ✅ Fetch Completed Task Results
def fetch_review_results(task_id):
    """Fetches completed review results from DataForSEO."""
    print(f"⏳ Waiting for DataForSEO to process task: {task_id}")

    url = f"https://api.dataforseo.com/v3/business_data/google/reviews/task_get/{task_id}"
    auth = (DATAFORSEO_USERNAME, DATAFORSEO_PASSWORD)

    max_retries = 10
    for attempt in range(max_retries):
        time.sleep(5)  # ✅ Wait before checking status

        response = requests.get(url, auth=auth)
        data = response.json()
        print(f"📡 DataForSEO Task Result: {data}")  # Debugging

        if "tasks" not in data or not data["tasks"]:
            continue

        task = data["tasks"][0]
        if task.get("status_code") == 20000 and task.get("result"):
            return task["result"][0].get("items", [])  # ✅ Extract reviews

        print(f"⏳ Task not ready yet (Attempt {attempt+1}/{max_retries})")

    print("❌ Task timed out. No reviews found.")
    return None

# ✅ Get Google Reviews
def get_google_reviews(business_name):
    """Fetches Google Reviews from DataForSEO asynchronously."""

    # ✅ Step 1: Get Place ID
    place_id = get_place_id(business_name)
    if not place_id:
        print("❌ No valid Place ID found.")
        return None  # Stop execution if no Place ID found

    # ✅ Step 2: Submit Task
    task_id = submit_review_task(place_id)
    if not task_id:
        return None  # Stop if task submission failed

    # ✅ Step 3: Fetch Task Results
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