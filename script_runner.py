import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

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

# ✅ TRUSTPILOT SCRAPER
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
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0 Safari/537.36",
                "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            review_cards = soup.find_all("div", class_="styles_cardWrapper__LcCPA")
            print(f"🔍 Found {len(review_cards)} review cards")

            if not review_cards:
                break  # Stop if no reviews are found

            for card in review_cards:
                # ✅ Extract review text
                comment_tag = card.find("p", class_="typography_body-l__KUYFJ")
                comment = comment_tag.get_text(strip=True) if comment_tag else "No review text"

                # ✅ Extract rating
                rating_tag = card.find("div", class_="star-rating_starRating__4rrcf")
                if rating_tag:
                    rating_text = rating_tag.find("img")["alt"]
                    rating_numbers = [word for word in rating_text.split() if word.isdigit()]
                    rating = int(rating_numbers[0]) if rating_numbers else None
                else:
                    rating = None

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
                        "Platform": "Trustpilot",
                        "Review": comment,
                        "Rating": rating,
                        "Keywords": ", ".join(matched_keywords),
                        "Publish Date": publish_date,
                        "Review Link": review_link
                    })

            current_page += 1
            time.sleep(2)

        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching page: {e}")
            break

    if not all_reviews:
        print("❌ No matching Trustpilot reviews found!")
        return None

    filename = get_unique_filename("trustpilot_reviews.xlsx")
    pd.DataFrame(all_reviews).to_excel(filename, index=False)
    print(f"✅ Scraped {len(all_reviews)} reviews into {filename}")
    return filename


# ✅ GOOGLE REVIEWS SCRAPER
def scrape_google(company_url, keywords, include_ratings):
    """Scrapes Google Reviews using Selenium."""
    
    print(f"🟡 Fetching Google reviews from {company_url}")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(company_url)
    time.sleep(5)  # Let the page load

    review_cards = driver.find_elements(By.CSS_SELECTOR, "div.bwb7ce")
    print(f"🔍 Found {len(review_cards)} Google review cards")

    if not review_cards:
        print("❌ No reviews found on this Google page.")
        driver.quit()
        return None

    all_reviews = []
    for card in review_cards:
        try:
            reviewer_name = card.find_element(By.CLASS_NAME, "Vpc5Fe").text
            review_text_element = card.find_elements(By.CLASS_NAME, "OA1nbd")
            review_text = review_text_element[0].text if review_text_element else "No review text"
            star_rating = len(card.find_elements(By.CLASS_NAME, "ePMStd"))

            # ✅ Extract review link
            link_tag = card.find_elements(By.TAG_NAME, "a")
            review_link = link_tag[0].get_attribute("href") if link_tag else "N/A"

            # ✅ Extract publish date
            date_tag = card.find_elements(By.CLASS_NAME, "y3Ibjb")
            publish_date = date_tag[0].text if date_tag else "N/A"

            matched_keywords = [k for k in keywords if k.lower() in review_text.lower()]
            if star_rating in include_ratings and matched_keywords:
                all_reviews.append({
                    "Platform": "Google Reviews",
                    "Review": review_text,
                    "Rating": star_rating,
                    "Keywords": ", ".join(matched_keywords),
                    "Publish Date": publish_date,
                    "Review Link": review_link
                })

        except Exception as e:
            print(f"❌ Error extracting review: {e}")

    driver.quit()

    if not all_reviews:
        print("❌ No matching Google reviews found!")
        return None

    filename = get_unique_filename("google_reviews.xlsx")
    pd.DataFrame(all_reviews).to_excel(filename, index=False)
    print(f"✅ Scraped {len(all_reviews)} reviews into {filename}")
    return filename


# ✅ MAIN RUNNER FUNCTION
def run_script(platform, company_url, keywords, include_ratings):
    """Runs the correct scraper based on user selection."""
    keywords = keywords.split(",")
    include_ratings = list(map(int, include_ratings.split(",")))

    if platform == "trustpilot":
        return scrape_trustpilot(company_url, keywords, include_ratings)
    elif platform == "google":
        return scrape_google(company_url, keywords, include_ratings)
    else:
        raise ValueError("❌ Invalid platform selected")