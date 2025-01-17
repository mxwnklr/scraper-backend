import os
import time
import pandas as pd
from serpapi import GoogleSearch

# ✅ Load API key from environment variables
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")

def get_google_reviews(place_id, min_rating=1):
    """Fetch all Google reviews using SerpAPI with pagination."""
    
    if not SERPAPI_KEY:
        return {"error": "❌ Missing SerpAPI key. Set 'SERPAPI_API_KEY' in environment variables."}

    all_reviews = []
    offset = 0  # Pagination starts at 0

    while True:
        params = {
            "engine": "google_maps_reviews",
            "place_id": place_id,
            "api_key": SERPAPI_KEY,
            "hl": "en",  # Language
            "sort_by": "newest",  # Sort by newest reviews
            "start": offset,  # Pagination
        }

        print(f"🔍 Fetching reviews (Offset: {offset})...")

        try:
            search = GoogleSearch(params)
            results = search.get_dict()

            if "error" in results:
                return {"error": f"SerpAPI Error: {results['error']}"}

            reviews = results.get("reviews", [])
            
            # ✅ Filter reviews by minimum rating
            filtered_reviews = [
                {
                    "Reviewer": r["user"]["name"],
                    "Rating": r["rating"],
                    "Review": r["snippet"]
                }
                for r in reviews if r["rating"] >= int(min_rating)
            ]

            if not filtered_reviews:
                break  # ✅ Stop fetching if no more reviews

            all_reviews.extend(filtered_reviews)

            # ✅ Break if there are no more pages
            if "next_page_token" not in results:
                print("✅ No more pages left to scrape.")
                break

            offset += 10  # Increase offset for the next set of reviews
            time.sleep(2)  # ✅ Prevent rate-limiting

        except Exception as e:
            return {"error": f"❌ Error fetching reviews: {str(e)}"}

    if not all_reviews:
        return None  # ✅ Return None if no reviews found

    # ✅ Save reviews to an Excel file
    filename = "google_reviews.xlsx"
    df = pd.DataFrame(all_reviews)
    df.to_excel(filename, index=False)
    
    print(f"📄 Saved {len(all_reviews)} reviews to {filename}")
    return filename