import requests
import os
import pandas as pd
import time

# ✅ Load API Keys
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
DATAFORSEO_USERNAME = os.getenv("DATAFORSEO_USERNAME")
DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")

# ✅ Get Google Place ID
def get_place_id(business_name, address=None):
    """Fetches Place ID from Google Places API based on business name & address."""
    print(f"🔍 Searching Google Places API for: {business_name}")

    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    input_text = f"{business_name}, {address}" if address else business_name

    params = {
        "input": input_text,
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
    if include_ratings and include_ratings.strip():
        filters.append({"rating": include_ratings.split(",")})
    if keywords and keywords.strip():
        filters.append({"text": keywords.split(",")})

    payload = [{
    "se": "google",
    "se_type": "reviews",
    "place_id": place_id,
    "reviews_limit": 5000,  # Increased from 2000
    "max_crawl_pages": 200,  # Increased from 100
    "depth": 1000,          # Increased from 700
    "filters": filters,  
    "language_code": "de",
    "location_name": "Germany",
    "device": "desktop",
    "os": "windows"
    }]

    if page_token:
        payload[0]["page_token"] = page_token  

    headers = {"Content-Type": "application/json"}
    response = requests.post(url, auth=auth, json=payload, headers=headers)
    data = response.json()

    # print(f"📡 DataForSEO Task Response: {data}")  # Debugging

    if "tasks" not in data or not data["tasks"]:
        print("❌ DataForSEO API returned an empty response.")
        return None

    task = data["tasks"][0]
    if task.get("status_code") != 20100:
        print(f"❌ DataForSEO Error: {task.get('status_message')}")
        return None

    task_id = task["id"]
    print(f"✅ Task Created: {task_id}")
    return task_id

# ✅ Fetch Completed Task Results & Format Output
def fetch_review_results(task_id, keywords):
    print(f"⏳ Waiting for DataForSEO to process task: {task_id}")
    url = f"https://api.dataforseo.com/v3/business_data/google/reviews/task_get/{task_id}"
    auth = (DATAFORSEO_USERNAME, DATAFORSEO_PASSWORD)
    
    reviews = []
    max_retries = 10
    retry_count = 0

    while True:
        time.sleep(5)
        
        try:
            response = requests.get(url, auth=auth)
            data = response.json()
            
            if "tasks" not in data or not data["tasks"]:
                print("❌ No valid tasks found.")
                if retry_count < max_retries:
                    retry_count += 1
                    continue
                return None

            task = data["tasks"][0]
            if task.get("status_code") == 20000 and task.get("result"):
                result = task["result"][0]
                
                # Print total reviews available
                if "total_count" in result:
                    print(f"📊 Total reviews available: {result['total_count']}")
                
                for item in result.get("items", []):
                    review_text = item.get("review_text", "")
                    review_rating = item.get("rating", {}).get("value", "")
                    review_date = item.get("timestamp", "")
                    review_url = item.get("review_url", "")
                    
                    reviews.append({
                        "Review": review_text,
                        "Rating": review_rating,  # Added rating to output
                        "Date": review_date,
                        "Link to review": review_url,
                    })

                print(f"✅ Scraped {len(reviews)} reviews so far...")
                
                next_page_token = result.get("next_page_token")
                if not next_page_token:
                    print("🏁 No more pages available")
                    break
                    
                print(f"🔄 Fetching next page of reviews...")
                new_task_id = submit_review_task(result["place_id"], "", "", next_page_token)
                if new_task_id:
                    task_id = new_task_id
                    url = f"https://api.dataforseo.com/v3/business_data/google/reviews/task_get/{task_id}"
                    retry_count = 0  # Reset retry count for new page
                else:
                    print("❌ Failed to get next page")
                    break
                    
            elif task.get("status_code") == 20100:
                print("⏳ Task still in progress...")
                time.sleep(3)
            else:
                print(f"❌ Task failed: {task.get('status_message')}")
                if retry_count < max_retries:
                    retry_count += 1
                    continue
                break
                
        except Exception as e:
            print(f"❌ Error fetching reviews: {str(e)}")
            if retry_count < max_retries:
                retry_count += 1
                continue
            break

    print(f"🎉 Total reviews collected: {len(reviews)}")
    return reviews

# ✅ Get Google Reviews (Handles Pagination & Formatting)
def get_google_reviews(business_name, address=None, include_ratings="", keywords=""):
    """Fetches Google Reviews from DataForSEO asynchronously, handling pagination & formatting."""

    # ✅ Step 1: Get Place ID
    place_id = get_place_id(business_name, address)
    if not place_id:
        print("❌ No valid Place ID found.")
        return None  

    # ✅ Step 2: Submit Task
    task_id = submit_review_task(place_id, include_ratings, keywords)
    if not task_id:
        return None  

    # ✅ Step 3: Fetch Task Results (All Pages)
    reviews = fetch_review_results(task_id, keywords)
    if not reviews:
        print("❌ No reviews found.")
        return None

    # ✅ Save reviews to Excel (Formatted)
    filename = "google_reviews_formatted.xlsx"
    df = pd.DataFrame(reviews)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")  # Format date

    df.to_excel(filename, index=False)
    
    print(f"✅ Successfully saved {len(reviews)} reviews to {filename}")
    return filename