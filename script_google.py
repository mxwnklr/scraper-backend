import requests
import pandas as pd
import os
from dotenv import load_dotenv

# Load API Key from .env
load_dotenv()
API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

def get_place_id(place_name):
    """Fetches the Place ID for a given place name using the Places API."""
    url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        'input': place_name,
        'inputtype': 'textquery',
        'fields': 'place_id',
        'key': API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()

    if 'candidates' in data and len(data['candidates']) > 0:
        return data['candidates'][0]['place_id']
    else:
        print(f"❌ No Place ID found for: {place_name}")
        return None

    # Convert to Excel
    df = pd.DataFrame(filtered_reviews)
    output_file = "google_reviews.xlsx"
    df.to_excel(output_file, index=False)
    print(f"✅ Saved {len(filtered_reviews)} reviews to {output_file}")
    return output_file