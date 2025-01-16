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

# ✅ Helper Function: Generate a unique filename
def get_unique_filename(base_name):
    """Generate a unique file name by appending a number if the file already exists."""
    if not os.path.exists(base_name):
        return base_name

    base, ext = os.path.splitext(base_name)
    counter = 1
    while os.path.exists(f"{base} ({counter}){ext}"):
        counter += 1
    return f"{base} ({counter}){ext}"

# ✅ Trustpilot Scraper
def scrape_trustpilot(company_url, keywords, include_ratings):
    reviews = []
    current_page = 1

    while True:
        url = f"{company_url}?page={current_page}"
        print(f"🟡 Fetching: {url}")

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        print(f"🟢 Response Status: {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        review_cards = soup.find_all("div", class_="styles_cardWrapper__LcCPA")
        print(f"🔍 Found {len(review_cards)} review cards")

        if not review_cards:
            print("❌ No more reviews found, stopping scraper.")
            break

        for review_card in review_cards:
            rating_tag = review_card.find("img")
            comment_tag = review_card.find("p", class_="typography_body-l__KUYFJ")

            if rating_tag and "alt" in rating_tag.attrs:
                rating_text = rating_tag["alt"]
                rating_numbers = [word for word in rating_text.split() if word.isdigit()]
                rating = int(rating_numbers[0]) if rating_numbers else None
            else:
                rating = None
            comment = comment_tag.get_text(strip=True) if comment_tag else ""

            matched_keywords = [k for k in keywords if k in comment.lower()]
            if rating in include_ratings and matched_keywords:
                reviews.append({
                    "Platform": "Trustpilot",
                    "Review": comment,
                    "Rating": rating,
                    "Keywords": ", ".join(matched_keywords)
                })

        current_page += 1
        time.sleep(2)

    if not reviews:
        print("❌ No matching reviews found!")
        return None

    filename = get_unique_filename("trustpilot_reviews.xlsx")
    pd.DataFrame(reviews).to_excel(filename, index=False)
    print(f"✅ Scraped {len(reviews)} reviews into {filename}")
    return filename

# ✅ Google Scraper
def scrape_google(company_url, keywords, include_ratings):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(company_url)
    time.sleep(5)

    print("🟡 Google page loaded")
    review_cards = driver.find_elements(By.CLASS_NAME, "bwb7ce")
    print(f"🔍 Found {len(review_cards)} Google review cards")

    if not review_cards:
        print("❌ No reviews found on this Google page.")
        driver.quit()
        return None

    reviews = []
    for card in review_cards:
        try:
            reviewer_name = card.find_element(By.CLASS_NAME, "Vpc5Fe").text
            review_text_element = card.find_elements(By.CLASS_NAME, "OA1nbd")
            review_text = review_text_element[0].text if review_text_element else "No comment"
            star_rating = len(card.find_elements(By.CLASS_NAME, "ePMStd"))

            matched_keywords = [k for k in keywords if k.lower() in review_text.lower()]
            if star_rating in include_ratings and matched_keywords:
                reviews.append({
                    "Platform": "Google Reviews",
                    "Reviewer": reviewer_name,
                    "Review": review_text,
                    "Rating": star_rating,
                    "Keywords": ", ".join(matched_keywords)
                })

        except Exception as e:
            print(f"Error extracting review: {e}")

    driver.quit()

    if not reviews:
        print("❌ No matching Google reviews found!")
        return None

    filename = get_unique_filename("google_reviews.xlsx")
    pd.DataFrame(reviews).to_excel(filename, index=False)
    print(f"✅ Scraped {len(reviews)} reviews into {filename}")
    return filename

# ✅ Main Runner: Calls the Correct Scraper Based on User Selection
def run_script(platform, company_url, keywords, include_ratings):
    keywords = keywords.split(",")  # Convert keywords string into a list
    include_ratings = list(map(int, include_ratings.split(",")))  # Convert rating string into a list of integers

    if platform == "trustpilot":
        return scrape_trustpilot(company_url, keywords, include_ratings)
    elif platform == "google":
        return scrape_google(company_url, keywords, include_ratings)
    else:
        raise ValueError("❌ Invalid platform selected")