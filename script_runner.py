import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

# Define a function to handle the scraping
def run_script(company_url, keywords, include_ratings):
    """
    Scrapes Trustpilot reviews based on the given parameters.
    - `company_url`: Trustpilot URL of the company.
    - `keywords`: List of keywords to filter reviews.
    - `include_ratings`: List of ratings (1-5) to include.
    Returns: Path to the saved Excel file.
    """

    OUTPUT_FILE_BASE = "uploads/trustpilot_comments.xlsx"  # Output file directory
    os.makedirs("uploads", exist_ok=True)  # Ensure the folder exists

    # Function to generate a unique filename
    def get_unique_filename(base_name):
        if not os.path.exists(base_name):
            return base_name
        
        base, ext = os.path.splitext(base_name)
        counter = 1
        while os.path.exists(f"{base} ({counter}){ext}"):
            counter += 1
        return f"{base} ({counter}){ext}"

    # Fetch page content
    def fetch_page_content(url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0 Safari/537.36",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text

    # Parse reviews
    def parse_reviews(html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        reviews = []
        
        for review_card in soup.find_all("div", class_="styles_cardWrapper__LcCPA"):
            rating_tag = review_card.find("div", class_="star-rating_starRating__4rrcf")
            if rating_tag:
                try:
                    rating = int([word for word in rating_tag.find("img")["alt"].split() if word.isdigit()][0])
                except IndexError:
                    rating = None
            else:
                rating = None

            comment_tag = review_card.find("p", class_="typography_body-l__KUYFJ")
            comment = comment_tag.get_text(strip=True) if comment_tag else ""

            link_tag = review_card.find("a", href=True)
            link = f"https://de.trustpilot.com{link_tag['href']}" if link_tag else ""

            date_tag = review_card.find("time", {"datetime": True})
            review_date = date_tag["datetime"] if date_tag else ""

            reviews.append({
                "rating": rating,
                "comment": comment,
                "link": link,
                "date": review_date
            })
        
        return reviews

    # Filter reviews by keywords and ratings
    def filter_reviews(reviews, keywords, include_ratings):
        filtered = []
        for review in reviews:
            matched_keywords = [keyword for keyword in keywords if keyword.lower() in review["comment"].lower()]
            if review["rating"] in include_ratings and matched_keywords:
                filtered.append({
                    "Comment": review["comment"],
                    "Rating": review["rating"],
                    "Keyword": ", ".join(matched_keywords),
                    "Link to Comment": review["link"],
                    "Date": review["date"]
                })
        return filtered

    # Start scraping
    current_page = 1
    all_filtered_reviews = []
    print(f"Starting to scrape Trustpilot: {company_url}")

    while True:
        url = f"{company_url}?page={current_page}"
        print(f"Fetching page {current_page}: {url}")
        
        try:
            html_content = fetch_page_content(url)
            reviews = parse_reviews(html_content)

            if not reviews:
                print("No more reviews found.")
                break

            filtered_reviews = filter_reviews(reviews, keywords, include_ratings)
            all_filtered_reviews.extend(filtered_reviews)

            current_page += 1
            time.sleep(2)  # Avoid rate limits
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page: {e}")
            break

    # Save results
    if all_filtered_reviews:
        unique_file_name = get_unique_filename(OUTPUT_FILE_BASE)
        df = pd.DataFrame(all_filtered_reviews)
        df.to_excel(unique_file_name, index=False)
        print(f"Filtered reviews saved to {unique_file_name}.")
        return unique_file_name
    else:
        print("No reviews matched the criteria.")
        return None