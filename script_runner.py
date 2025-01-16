import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re  # ✅ Import regex for partial class matching

# ✅ Helper Function: Ensure Unique Filename
def get_unique_filename(base_name):
    """Generate a unique file name by appending a number if the file already exists."""
    if not os.path.exists(base_name):
        return base_name

    base, ext = os.path.splitext(base_name)
    counter = 1
    while os.path.exists(f"{base} ({counter}){ext}"):
        counter += 1
    return f"{base} ({counter}){ext}"

# ✅ TRUSTPILOT SCRAPER with Partial Class Matching
def scrape_trustpilot(company_url, keywords, include_ratings):
    """Scrapes Trustpilot reviews based on keywords and ratings."""
    current_page = 1
    all_reviews = []

    print(f"🟡 Fetching Trustpilot reviews from {company_url}")

    while True:
        url = f"{company_url}?page={current_page}"
        print(f"🔵 Scraping page {current_page}: {url}")

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # ✅ Dynamically find all review cards (handles changing class names)
            review_cards = soup.find_all("div", class_=re.compile("styles_cardWrapper"))
            print(f"🔍 Found {len(review_cards)} review cards")

            if not review_cards:
                break  # Stop if no reviews are found

            for card in review_cards:
                # ✅ Extract review text (handles dynamic class names)
                comment_tag = card.find("p", class_=re.compile("typography_body"))
                comment = comment_tag.get_text(strip=True) if comment_tag else "No review text"

                # ✅ Extract rating (handles dynamic class names)
                rating_tag = card.find("div", class_=re.compile("star-rating_starRating"))
                rating_img = rating_tag.find("img") if rating_tag else None
                rating = None

                if rating_img and "alt" in rating_img.attrs:
                    rating_text = rating_img["alt"]
                    rating_numbers = [word for word in rating_text.split() if word.isdigit()]
                    rating = int(rating_numbers[0]) if rating_numbers else None

                # ✅ Extract review link
                link_tag = card.find("a", href=True)
                review_link = f"https://de.trustpilot.com{link_tag['href']}" if link_tag else "N/A"

                # ✅ Extract publish date
                date_tag = card.find("time", {"datetime": True})
                publish_date = date_tag["datetime"] if date_tag else "N/A"

                # ✅ Filter by keywords and rating
                matched_keywords = [k for k in keywords if k.lower() in comment.lower()]
                if rating in include_ratings and matched_keywords:
                    all_reviews.append({
                        "Review": comment,
                        "Rating": rating,
                        "Keywords": ", ".join(matched_keywords),
                        "Publish Date": publish_date,
                        "Review Link": review_link
                    })

            current_page += 1
            time.sleep(2)  # Prevent request bans

        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching page: {e}")
            break

    if not all_reviews:
        print("❌ No matching Trustpilot reviews found!")
        return None

    # ✅ Ensure the data is saved correctly as an Excel file
    filename = get_unique_filename("trustpilot_reviews.xlsx")
    df = pd.DataFrame(all_reviews)

    # Use ExcelWriter explicitly
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    print(f"✅ Scraped {len(all_reviews)} reviews into {filename}")
    return filename

# ✅ MAIN RUNNER FUNCTION (Only Trustpilot)
def run_script(company_url, keywords, include_ratings):
    """Runs the Trustpilot scraper (Google removed)."""
    keywords = keywords.split(",")
    include_ratings = list(map(int, include_ratings.split(",")))

    return scrape_trustpilot(company_url, keywords, include_ratings)