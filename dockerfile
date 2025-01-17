# Use official Python image
FROM python:3.11

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install dependencies for Chrome & ChromeDriver
RUN apt-get update && apt-get install -y wget unzip curl \
    && wget -q -O google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome.deb || apt-get -fy install \
    && wget -q "https://chromedriver.storage.googleapis.com/$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE)/chromedriver_linux64.zip" \
    && unzip chromedriver_linux64.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf /var/lib/apt/lists/* google-chrome.deb chromedriver_linux64.zip

# Expose port
EXPOSE 8000

# Copy app code
COPY . .

# Start app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]