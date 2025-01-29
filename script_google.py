import requests
import os
import pandas as pd
import time
from apify_client import ApifyClient

# Load API Keys
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

# Initialize Apify client
apify_client = ApifyClient(APIFY_API_TOKEN)

def get_place_id(business_name, address=None):
    """Fetches Place ID from Google Places API based on business name & address."""
    print(f"🔍 Searching Google Places API for: {business_name}")

    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    input_text = f"{business_name}, {address}" if address else business_name

    params = {
        "input": input_text,
        "inputtype": "textquery",
        "fields": "place_id",
        "key": GOOGLE_PLACES_API_KEY
    }

    response = requests.get(url, params=params)
    data = response.json()
    print(f"🔎 Google Places Response: {data}")

    if data.get("status") == "OK" and data.get("candidates"):
        return data["candidates"][0]["place_id"]
    else:
        print("❌ Error extracting Place ID: No result found in API response.")
        return None

def get_reviews_apify(place_id, max_reviews=1000):
    """Fetch reviews using Apify API."""
    print(f"📡 Fetching reviews from Apify for Place ID: {place_id}")
    
    try:
        run_input = {
            "placeIds": [place_id],
            "maxReviews": max_reviews,
            "language": "en",
            "reviewsSort": "newest"
        }

        print("⏳ Starting Apify actor...")
        run = apify_client.actor("compass/google-maps-reviews-scraper").call(run_input=run_input)
        
        if not run:
            print("❌ Apify run failed to start")
            return None

        run_id = run["id"]
        dataset_id = run["defaultDatasetId"]
        print(f"✅ Apify run started with ID: {run_id}")
        
        max_wait_time = 180  # 3 minutes
        wait_start = time.time()
        
        while True:
            if time.time() - wait_start > max_wait_time:
                print("❌ Timeout waiting for Apify results")
                return None
                
            run_info = apify_client.run(run_id).get()
            status = run_info.get("status")
            print(f"🔄 Run status: {status}")
            
            if status == "SUCCEEDED":
                dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?format=json&clean=1&token={APIFY_API_TOKEN}"
                response = requests.get(dataset_url)
                
                if response.status_code != 200:
                    print(f"❌ Failed to fetch dataset: {response.status_code}")
                    return None
                
                dataset_items = response.json()
                print(f"🔍 Dataset items fetched: {len(dataset_items)} items")
                
                # Extract specific fields and save to Excel
                reviews = [
                    {
                        "Text": item.get("text"),
                        "Date": item.get("date"),
                        "Rating": item.get("rating"),
                        "Link to Review": item.get("link")
                    }
                    for item in dataset_items
                ]
                
                return save_reviews_to_excel(reviews)
                
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                print(f"❌ Run failed with status: {status}")
                return None
                
            time.sleep(5)  # Wait 5 seconds before checking again
            
    except Exception as e:
        print(f"❌ Error in Apify scraping: {str(e)}")
        return None

def save_reviews_to_excel(reviews):
    """Save reviews to an Excel file."""
    try:
        # Ensure reviews is a list of dictionaries
        if not isinstance(reviews, list) or not all(isinstance(review, dict) for review in reviews):
            raise ValueError("Reviews data is not a list of dictionaries")

        filename = "google_reviews.xlsx"
        df = pd.DataFrame(reviews)
        df.to_excel(filename, index=False)
        print(f"✅ Successfully saved {len(reviews)} reviews to {filename}")
        return filename
    except Exception as e:
        print(f"❌ Error saving to Excel: {str(e)}")
        return None

def get_google_reviews(business_name, address=None):
    """Main function to fetch and filter Google Reviews."""
    
    # Get Place ID
    place_id = get_place_id(business_name, address)
    if not place_id:
        print("❌ No valid Place ID found.")
        return None

    # Get reviews from Apify
    filename = get_reviews_apify(place_id)
    if not filename:
        print("❌ No reviews found.")
        return None
        
    print(f"✅ Reviews saved to {filename}")
    return filename