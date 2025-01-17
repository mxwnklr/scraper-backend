from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import json
import time
import os
import shutil

# ✅ Set Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--no-sandbox")  # Required for Docker
chrome_options.add_argument("--disable-dev-shm-usage")  # Prevent crashes
chrome_options.add_argument("--disable-gpu")  # Optional: Avoid GPU rendering issues
chrome_options.add_argument("--remote-debugging-port=9222")  # Debugging

# ✅ Set ChromeDriver path (ensure it's correctly installed)
chrome_driver_path = "/usr/local/bin/chromedriver"
chrome_service = Service(chrome_driver_path)

# ✅ Initialize WebDriver
driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

print("✅ ChromeDriver is running successfully!")
# ✅ Function to Extract Google Review URLs
def get_google_review_urls(search_term):
    formatted_search = search_term.replace(" ", "+")
    driver.get(f"https://www.google.com/maps/search/{formatted_search}")

    time.sleep(3)  # Allow page to load

    try:
        results = driver.find_element(By.XPATH, f'//div[@aria-label="Results for {search_term}"]')
        anchor_tags = results.find_elements(By.XPATH, "//a[@class='hfpxzc']")
        
        urls = [tag.get_attribute("href") for tag in anchor_tags[:10]]  # Get first 10 links
        return urls

    except Exception as e:
        print(f"❌ Error finding search results: {e}")
        return []

# ✅ Function to Extract Google Reviews from URLs
def extract_google_reviews(urls):
    all_reviews = []

    for url in urls:
        try:
            driver.get(url)
            time.sleep(2)

            # Click "Reviews" tab
            driver.find_element(By.XPATH, '//div[contains(text(),"Reviews")]').click()
            time.sleep(3)

            # Scroll to load more reviews
            review_area = driver.find_element(By.XPATH, '//div[@class="m6QErb DxyBCb kA9KIf dS8AEf XiKgde "]')

            for _ in range(3):  # Scroll 3 times
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", review_area)
                time.sleep(2)

            # Extract review elements
            review_elements = driver.find_elements(By.XPATH, "//div[@class='jftiEf fontBodyMedium ']")

            for review in review_elements:
                all_reviews.append({
                    "Reviewer": review.find_element(By.CLASS_NAME, 'd4r55 ').text,
                    "About": review.find_element(By.CLASS_NAME, 'RfnDt ').text,
                    "Rating": review.find_element(By.CLASS_NAME, 'kvMYJc').get_attribute('aria-label'),
                    "Reviewed On": review.find_element(By.CLASS_NAME, 'rsqaWe').text,
                    "Review Text": review.find_element(By.CLASS_NAME, 'MyEned').text
                })

        except Exception as e:
            print(f"❌ Error extracting reviews: {e}")
            continue

    return all_reviews