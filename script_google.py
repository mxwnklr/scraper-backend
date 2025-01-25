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

def get_reviews_apify(place_id, max_reviews=1000):
    print(f"📡 Fetching reviews from Apify for Place ID: {place_id}")
    
    try:
        run_input = {
            "placeIds": [place_id],
            "maxCrawledPlacesPerSearch": 1,
            "maxReviews": max_reviews,
            "language": "de",
            "reviewsSort": "newest",
            "maxImages": 0
        }

        # Start the actor and wait for it to finish
        print("⏳ Starting Apify actor...")
        run = apify_client.actor("compass/google-maps-reviews-scraper").call(run_input=run_input)
        
        if not run:
            print("❌ Apify run failed to start")
            return None

        print(f"✅ Apify run started with ID: {run['id']}")
        
        # Wait for the run to finish
        print("⏳ Waiting for results...")
        while True:
            run_info = apify_client.run(run["id"]).get()
            if run_info["status"] == "SUCCEEDED":
                break
            elif run_info["status"] in ["FAILED", "ABORTED", "TIMED-OUT"]:
                print(f"❌ Apify run failed with status: {run_info['status']}")
                return None
            time.sleep(2)  # Wait 2 seconds before checking again
        
        # Now fetch the results
        print("📥 Downloading results...")
        reviews_list = []
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            if "reviews" in item:
                for review in item["reviews"]:
                    reviews_list.append({
                        "Review": review.get("text", ""),
                        "Rating": review.get("stars", ""),
                        "Date": review.get("publishedAtDate", ""),
                        "Link to review": review.get("reviewUrl", "")
                    })
        
        print(f"✅ Successfully fetched {len(reviews_list)} reviews")
        return reviews_list if reviews_list else None
        
    except Exception as e:
        print(f"❌ Error in Apify scraping: {str(e)}")
        return None

def get_google_reviews(business_name, address=None, include_ratings="", keywords=""):
    """Main function to fetch Google Reviews using Apify"""
    
    # ✅ Step 1: Get Place ID
    place_id = get_place_id(business_name, address)
    if not place_id:
        print("❌ No valid Place ID found.")
        return None

    # ✅ Step 2: Get reviews from Apify
    reviews = get_reviews_apify(place_id)
    if not reviews:
        print("❌ No reviews found.")
        return None

    print(f"🔍 Found {len(reviews)} reviews, applying filters...")

    # ✅ Step 3: Filter reviews if needed
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

    # ✅ Save reviews to Excel
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