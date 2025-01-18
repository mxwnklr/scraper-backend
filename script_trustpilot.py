import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re

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

### **✅ TRUSTPILOT SCRAPER FUNCTION**
def run_trustpilot_scraper(company_url, keywords, include_ratings):
    """Scrapes Trustpilot reviews based on keywords and ratings. If left empty, scrapes all reviews."""
    current_page = 1
    all_reviews = []

    print(f"🟡 Fetching Trustpilot reviews from {company_url}")

    # ✅ Convert include_ratings to a list of integers (if provided)
    include_ratings = list(map(int, include_ratings.split(","))) if include_ratings else []
    keywords_list = [k.strip().lower() for k in keywords.split(",")] if keywords else []

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

            review_cards = soup.find_all("div", class_=re.compile("styles_cardWrapper"))
            print(f"🔍 Found {len(review_cards)} review cards")

            if not review_cards:
                break  # Stop if no more reviews are found

            for card in review_cards:
                # ✅ Extract Review Text
                comment_tag = card.find("p", class_=re.compile("typography_body"))
                comment = comment_tag.get_text(strip=True) if comment_tag else "No review text"

                # ✅ Extract Rating
                rating_tag = card.find("div", class_=re.compile("star-rating_starRating"))
                rating_img = rating_tag.find("img") if rating_tag else None
                rating = None

                if rating_img and "alt" in rating_img.attrs:
                    rating_text = rating_img["alt"]
                    rating_numbers = [word for word in rating_text.split() if word.isdigit()]
                    rating = int(rating_numbers[0]) if rating_numbers else None

                # ✅ Extract Date
                date_tag = card.find("time")
                review_date = date_tag["datetime"] if date_tag else "Unknown Date"

                # ✅ Extract Review Link
                review_link_tag = card.find("a", href=True)
                review_link = f"https://www.trustpilot.com{review_link_tag['href']}" if review_link_tag else "No Link"

                # ✅ Keyword Filtering (if applicable)
                matched_keywords = [k for k in keywords_list if k in comment.lower()] if keywords_list else []

                # ✅ Apply Filters:
                if (not include_ratings or rating in include_ratings) and (not keywords_list or matched_keywords):
                    all_reviews.append({
                        "Review": comment,
                        "Rating": rating,
                        "Keyword": ", ".join(matched_keywords) if matched_keywords else "N/A",
                        "Date": review_date,
                        "Link to Review": review_link
                    })

            current_page += 1
            time.sleep(2)  # Prevent request bans

        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching page: {e}")
            break

    if not all_reviews:
        print("❌ No matching Trustpilot reviews found!")
        return None

    # ✅ Save results to Excel
    filename = get_unique_filename("trustpilot_reviews.xlsx")
    df = pd.DataFrame(all_reviews)
    df.to_excel(filename, index=False)

    print(f"✅ Successfully saved {len(all_reviews)} reviews to {filename}")
    return filename