#!/usr/bin/env bash

# ✅ Update package list
apt-get update && apt-get install -y wget unzip curl

# ✅ Install Google Chrome (without sudo)
echo "Installing Google Chrome..."
wget -q -O google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -i google-chrome.deb || apt-get install -fy
rm google-chrome.deb

# ✅ Verify Chrome installation
if command -v google-chrome > /dev/null; then
    echo "✅ Google Chrome installed at: $(command -v google-chrome)"
    google-chrome --version
else
    echo "❌ Google Chrome installation failed!"
    exit 1
fi

# ✅ Install ChromeDriver (without sudo)
echo "Installing ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d '.' -f 1)
CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION)
wget -q "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
unzip chromedriver_linux64.zip
chmod +x chromedriver
mv chromedriver /usr/local/bin/chromedriver
rm chromedriver_linux64.zip

# ✅ Verify ChromeDriver installation
if command -v chromedriver > /dev/null; then
    echo "✅ ChromeDriver installed at: $(command -v chromedriver)"
    chromedriver --version
else
    echo "❌ ChromeDriver installation failed!"
    exit 1
fi

echo "✅ Chrome and ChromeDriver installed successfully!"