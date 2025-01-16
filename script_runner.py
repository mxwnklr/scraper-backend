import os
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Helper Function: Generate unique filename
def get_unique_filename(base_name):
    """Generates a unique filename if the file already exists."""
    if not os.path.exists(base_name):
        return base_name
    base, ext = os.path.splitext(base_name)
    counter = 1
    while os.path.exists(f"{base} ({counter}){ext}"):
        counter += 1
    return f"{base} ({counter}){ext}"

# ✅ Trustpilot Scraper (Uses Requests + BeautifulSoup)
def scrape_trustpilot(company_url, keywords, include_ratings):
    reviews = []
    current_page = 1

    while True:
        url = f"{company_url}?page={current_page}"
        print(f"Fetching: {url}")  # ✅ Debugging output

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        found_reviews = False

        for review_card in soup.find_all("div", class_="styles_cardWrapper__LcCPA"):
            found_reviews = True  # ✅ Mark that reviews were found
            rating_tag = review_card.find("img")
            comment_tag = review_card.find("p", class_="typography_body-l__KUYFJ")

            rating = int([word for word in rating_tag["alt"].split() if word.isdigit()][0]) if rating_tag else None
            comment = comment_tag.get_text(strip=True) if comment_tag else ""

            matched_keywords = [k for k in keywords if k in comment.lower()]
            if rating in include_ratings and matched_keywords:
                reviews.append({
                    "Platform": "Trustpilot",
                    "Review": comment,
                    "Rating": rating,
                    "Keywords": ", ".join(matched_keywords)
                })

        if not found_reviews:
            print("No more reviews found, stopping scraper.")  # ✅ Debugging output
            break  # ✅ Stop scraping if no reviews found

        current_page += 1
        time.sleep(2)  # ✅ Prevent request throttling

    if not reviews:
        print("❌ No matching reviews found!")
        return None  # ✅ Don't generate an empty file

    filename = get_unique_filename("trustpilot_reviews.xlsx")
    pd.DataFrame(reviews).to_excel(filename, index=False)
    print(f"✅ Scraped {len(reviews)} reviews into {filename}")
    return filename

# ✅ Google Reviews Scraper (Uses Selenium)
def scrape_google(company_url, keywords, include_ratings):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(company_url)
    time.sleep(5)  # ✅ Let page load fully

    reviews = []
    review_cards = driver.find_elements(By.CLASS_NAME, "bwb7ce")

    if not review_cards:
        print("❌ No reviews found on this Google page.")
        driver.quit()
        return None  # ✅ Prevent empty file creation

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
        return None  # ✅ Don't create an empty file

    filename = get_unique_filename("google_reviews.xlsx")
    pd.DataFrame(reviews).to_excel(filename, index=False)
    print(f"✅ Scraped {len(reviews)} reviews into {filename}")
    return filename