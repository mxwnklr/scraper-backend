import requests
import os
import pandas as pd
import time
from apify_client import ApifyClient

# ✅ Load API Keys
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

# Initialize Apify client
apify_client = ApifyClient(APIFY_API_TOKEN)

# ✅ Get Google Place ID (keeping your existing function)
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
    print(f"🔎 Google Places Response: {data}")

    if data.get("status") == "OK" and data.get("candidates"):
        place_id = data["candidates"][0]["place_id"]
        address = data["candidates"][0]["formatted_address"]
        print(f"✅ Found Place ID: {place_id} for {business_name} ({address})")
        return place_id
    else:
        print("❌ Error extracting Place ID: No result found in API response.")
        return None

def process_reviews(dataset_items):
    """Process and format reviews from dataset items."""
    reviews_list = []
    for item in dataset_items:
        if "text" in item and "stars" in item and "publishedAtDate" in item and "reviewUrl" in item:
            reviews_list.append({
                "Review": item.get("text", ""),
                "Rating": item.get("stars", ""),
                "Date": item.get("publishedAtDate", ""),
                "Link to review": item.get("reviewUrl", "")
            })
    return reviews_list

def save_reviews_to_excel(reviews):
    """Save reviews to an Excel file."""
    try:
        filename = "google_reviews_formatted.xlsx"
        df = pd.DataFrame(reviews)
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
        df.to_excel(filename, index=False)
        print(f"✅ Successfully saved {len(reviews)} reviews to {filename}")
        return filename
    except Exception as e:
        print(f"❌ Error saving to Excel: {str(e)}")
        return None

def get_reviews_apify(place_id, max_reviews=1000):
    """Fetch reviews using Apify API."""
    print(f"📡 Fetching reviews from Apify for Place ID: {place_id}")
    
    try:
        # Start a new run
        run_input = {
            "placeIds": [place_id],
            "maxReviews": max_reviews,
            "language": "de",
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
        
        # Wait for the run to finish
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
                # Fetch results using dataset ID
                dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_API_TOKEN}"
                response = requests.get(dataset_url)
                
                if response.status_code != 200:
                    print(f"❌ Failed to fetch dataset: {response.status_code}")
                    return None
                
                dataset_items = response.json()
                if not dataset_items:
                    print("❌ No items found in dataset")
                    return None
                
                reviews_list = process_reviews(dataset_items)
                if reviews_list:
                    print(f"✅ Successfully fetched {len(reviews_list)} reviews")
                    return save_reviews_to_excel(reviews_list)
                else:
                    print("❌ No reviews found in dataset items")
                    return None
                
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                print(f"❌ Run failed with status: {status}")
                return None
                
            time.sleep(5)  # Wait 5 seconds before checking again
            
    except Exception as e:
        print(f"❌ Error in Apify scraping: {str(e)}")
        return None

def get_google_reviews(business_name, address=None, include_ratings="", keywords=""):
    """Main function to fetch and filter Google Reviews."""
    
    # Get Place ID
    place_id = get_place_id(business_name, address)
    if not place_id:
        print("❌ No valid Place ID found.")
        return None

    # Get reviews from Apify
    reviews = get_reviews_apify(place_id)
    if not reviews:
        print("❌ No reviews found.")
        return None

    print(f"🔍 Found {len(reviews)} reviews, applying filters...")

    # Apply filters if specified
    if keywords or include_ratings:
        filtered_reviews = []
        ratings_filter = [int(r.strip()) for r in include_ratings.split(",")] if include_ratings else []
        keywords_list = [k.strip().lower() for k in keywords.split(",")] if keywords else []
        
        for review in reviews:
            # Filter by rating
            if ratings_filter and int(float(review["Rating"])) not in ratings_filter:
                continue
                
            # Filter by keywords
            if keywords_list and not any(kw in review["Review"].lower() for kw in keywords_list):
                continue
                
            filtered_reviews.append(review)
        reviews = filtered_reviews
        print(f"✅ After filtering: {len(reviews)} reviews match criteria")

    if not reviews:
        print("❌ No reviews match the filter criteria")
        return None

    # Debugging: Print the reviews list to ensure it's correctly structured
    print(f"📝 Reviews to be saved: {reviews}")

    # Save to Excel
    try:
        filename = "google_reviews_formatted.xlsx"
        df = pd.DataFrame(reviews)
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
        df.to_excel(filename, index=False)
        print(f"✅ Successfully saved {len(reviews)} reviews to {filename}")
        return filename
    except Exception as e:
        print(f"❌ Error saving to Excel: {str(e)}")
        return None