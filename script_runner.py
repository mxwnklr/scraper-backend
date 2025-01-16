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
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        for review_card in soup.find_all("div", class_="styles_cardWrapper__LcCPA"):
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

        if not soup.find("div", class_="styles_cardWrapper__LcCPA"):
            break
        current_page += 1
        time.sleep(2)

    filename = get_unique_filename("trustpilot_reviews.xlsx")
    pd.DataFrame(reviews).to_excel(filename, index=False)
    return filename

# ✅ Google Reviews Scraper (Uses Selenium)
def scrape_google(company_url, keywords, include_ratings):
    options = Options()
    options.add_argument("--headless")  # Run in headless mode (no UI)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(company_url)
    time.sleep(3)  # Allow the page to load

    reviews = []
    review_cards = driver.find_elements(By.CLASS_NAME, "bwb7ce")  # Find all review elements

    for card in review_cards:
        try:
            # Extract reviewer name
            reviewer_name = card.find_element(By.CLASS_NAME, "Vpc5Fe").text

            # Extract review text
            review_text_element = card.find_elements(By.CLASS_NAME, "OA1nbd")
            review_text = review_text_element[0].text if review_text_element else "No comment"

            # Extract star rating (count the number of filled stars)
            star_rating = len(card.find_elements(By.CLASS_NAME, "ePMStd"))

            # Extract review date
            review_date_element = card.find_elements(By.CLASS_NAME, "y3Ibjb")
            review_date = review_date_element[0].text if review_date_element else "Unknown"

            # Extract review link
            review_link_element = card.find_elements(By.CLASS_NAME, "yC3ZMb")
            review_link = review_link_element[0].get_attribute("href") if review_link_element else "No link"

            # Check if review contains keywords and matches rating criteria
            matched_keywords = [k for k in keywords if k.lower() in review_text.lower()]
            if star_rating in include_ratings and matched_keywords:
                reviews.append({
                    "Platform": "Google Reviews",
                    "Reviewer": reviewer_name,
                    "Review": review_text,
                    "Rating": star_rating,
                    "Date": review_date,
                    "Link": review_link,
                    "Keywords": ", ".join(matched_keywords)
                })

        except Exception as e:
            print(f"Error extracting review: {e}")
            continue

    driver.quit()

    filename = get_unique_filename("google_reviews.xlsx")
    pd.DataFrame(reviews).to_excel(filename, index=False)
    return filename

# ✅ Main Runner: Calls the Correct Scraper Based on User Selection
def run_script(platform, company_url, keywords, include_ratings):
    keywords = keywords.split(",")
    include_ratings = list(map(int, include_ratings.split(",")))

    if platform == "trustpilot":
        return scrape_trustpilot(company_url, keywords, include_ratings)
    elif platform == "google":
        return scrape_google(company_url, keywords, include_ratings)
    else:
        raise ValueError("Invalid platform selected")